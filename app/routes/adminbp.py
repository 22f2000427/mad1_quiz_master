from flask import Blueprint, render_template, request, redirect, url_for, flash , send_file , send_from_directory
from flask_login import login_required, current_user
from models.models import db, Subjects, Chapters, Quizzes, Questions, Options, Users , QuizAttempts 
from datetime import datetime
from sqlalchemy.sql import func
from matplotlib import pyplot as plt
import io
import base64

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def restrict_to_admin():
    if current_user.role != "admin":
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("user_bp.user_dashboard"))


@admin_bp.route("/dashboard")
def admin_dashboard():
    
    total_subjects = Subjects.query.count()

    
    total_chapters = Chapters.query.count()

    
    total_quizzes = Quizzes.query.count()

    
    subjects = Subjects.query.all()
    subject_data = []

    for subject in subjects:
        chapters = Chapters.query.filter_by(subject_id=subject.id).all()
        chapter_data = []
        
        for chapter in chapters:
            question_count = Questions.query.join(Quizzes).filter(Quizzes.chapter_id == chapter.id).count()
            chapter_data.append({
                "id": chapter.id,
                "name": chapter.name,
                "question_count": question_count
            })

        subject_data.append({
            "id": subject.id,
            "name": subject.name,
            "chapters": chapter_data
        })

    return render_template("admin/admin_dashboard.html", subjects=subject_data)


@admin_bp.route("/quizzes", methods=["GET"])
def quiz_management():
    search_query = request.args.get("search", "").strip()
    quizzes = Quizzes.query

    if search_query:
        quizzes = quizzes.filter(Quizzes.title.ilike(f"%{search_query}%"))

    quizzes = quizzes.all()
    return render_template("admin/quiz_management.html", quizzes=quizzes)



@admin_bp.route("/new_subject", methods=["GET", "POST"])
def new_subject():
    if request.method == "POST":
        name = request.form.get("name").strip()
        description = request.form.get("description").strip()

        if not name:
            flash("Subject name is required!", "danger")
            return redirect(url_for("admin_bp.new_subject"))

        if Subjects.query.filter_by(name=name).first():
            flash("Subject already exists!", "danger")
        else:
            new_subject = Subjects(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            flash("New Subject added successfully!", "success")

        return redirect(url_for("admin_bp.admin_dashboard"))

    return render_template("admin/add_subject.html")


@admin_bp.route("/delete_subject/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    subject = Subjects.query.get_or_404(subject_id)

    
    chapters = Chapters.query.filter_by(subject_id=subject_id).all()
    for chapter in chapters:
        Quizzes.query.filter(Quizzes.chapter_id == chapter.id).delete()
        Chapters.query.filter_by(id=chapter.id).delete()

    db.session.delete(subject)
    db.session.commit()
    flash("Subject and all related chapters and quizzes deleted successfully!", "success")
    
    return redirect(url_for("admin_bp.admin_dashboard"))


@admin_bp.route("/new_chapter", methods=["GET", "POST"])
def new_chapter():
    subjects = Subjects.query.all()

    if request.method == "POST":
        name = request.form.get("name").strip()
        subject_id = request.form.get("subject_id")

        if not name or not subject_id:
            flash("Chapter name and subject selection are required!", "danger")
            return redirect(url_for("admin_bp.new_chapter"))

        if Chapters.query.filter_by(name=name, subject_id=subject_id).first():
            flash("Chapter already exists!", "danger")
        else:
            new_chapter = Chapters(name=name, subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()
            flash("New Chapter added successfully!", "success")

        return redirect(url_for("admin_bp.admin_dashboard"))

    return render_template("admin/add_chapter.html", subjects=subjects)


@admin_bp.route("/delete_chapter/<int:chapter_id>", methods=["POST"])
def delete_chapter(chapter_id):
    chapter = Chapters.query.get_or_404(chapter_id)

    
    Quizzes.query.filter(Quizzes.chapter_id == chapter_id).delete()

    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter and all related quizzes deleted successfully!", "success")

    return redirect(url_for("admin_bp.admin_dashboard"))

@admin_bp.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapters.query.get_or_404(chapter_id)

    if request.method == 'POST':
        chapter.name = request.form['name']
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin_bp.admin_dashboard'))  

    return render_template('admin/edit_chapter.html', chapter=chapter)



@admin_bp.route("/add_quiz", methods=["GET", "POST"])
def add_quiz():
    chapters = Chapters.query.all()

    if request.method == "POST":
        title = request.form.get("title").strip()
        chapter_id = request.form.get("chapter_id")
        scheduled_date = request.form.get("date")
        duration = request.form.get("duration")

        if not title or not chapter_id or not scheduled_date:
            flash("Title, Chapter, and Date are required!", "danger")
            return redirect(url_for("admin_bp.add_quiz"))

        try:
            new_quiz = Quizzes(
                title=title, 
                chapter_id=int(chapter_id), 
                scheduled_date=datetime.strptime(scheduled_date, "%Y-%m-%d"),
                duration=int(duration) if duration else 0,
                creator_id=current_user.id 
            )
            db.session.add(new_quiz)
            db.session.commit()
            flash("New Quiz added successfully!", "success")
            return redirect(url_for("admin_bp.quiz_management"))
        except ValueError:
            flash("Invalid input. Please check your data.", "danger")

    return render_template("admin/add_quiz.html", chapters=chapters)


@admin_bp.route("/delete_quiz/<int:quiz_id>", methods=["POST"])
def delete_quiz(quiz_id):
    quiz = Quizzes.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully!", "success")
    
    return redirect(url_for("admin_bp.quiz_management"))

@admin_bp.route('/quiz/<int:quiz_id>/questions')
def manage_questions(quiz_id):
    """ Display all questions for a quiz """
    quiz = Quizzes.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin/manage_questions.html', quiz=quiz, questions=questions)

@admin_bp.route('/admin/question/add/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    if request.method == 'POST':
        question_text = request.form['question_text']
        options = request.form.getlist('option_text[]')
        correct_index = int(request.form['correct_option'])

        new_question = Questions(quiz_id=quiz_id, text=question_text)
        db.session.add(new_question)
        db.session.commit()

        
        for index, option_text in enumerate(options):
            option = Options(
                question_id=new_question.id,
                text=option_text,
                is_correct=(index == correct_index)
            )
            db.session.add(option)
        
        db.session.commit()
        return redirect(url_for('admin_bp.manage_questions', quiz_id=quiz_id))

    return render_template('admin/add_question.html', quiz_id=quiz_id)

@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    """ Edit an existing question """
    question = Questions.query.get_or_404(question_id)
    options = Options.query.filter_by(question_id=question.id).all()

    if request.method == 'POST':
        question.text = request.form['question_text']

        
        for i, option in enumerate(options):
            option.text = request.form[f'option_{i}']
            option.is_correct = (i == int(request.form['correct_option']))

        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_bp.manage_questions', quiz_id=question.quiz_id))

    return render_template('admin/edit_question.html', question=question, options=options)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    """ Delete a question """
    question = Questions.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'danger')
    return redirect(url_for('admin_bp.manage_questions', quiz_id=quiz_id))



@admin_bp.route('/admin/users')
def user_management():
    search_query = request.args.get('search', '').strip()

    if search_query:
        users = Users.query.filter(
            (Users.full_name.ilike(f"%{search_query}%")) |
            (Users.username.ilike(f"%{search_query}%")) |  
            (Users.email.ilike(f"%{search_query}%")) |  
            (Users.qualification.ilike(f"%{search_query}%")) |  
            (Users.role.ilike(f"%{search_query}%"))  
        ).order_by(Users.full_name.asc()).all()
    else:
        users = Users.query.order_by(Users.full_name.asc()).all()

    return render_template('admin/user_management.html', users=users)



@admin_bp.route("/admin/users/<int:user_id>")
def user_details(user_id):
    user = Users.query.get_or_404(user_id)

    
    quiz_attempts = (
        QuizAttempts.query
        .filter_by(user_id=user_id)
        .join(Quizzes, QuizAttempts.quiz_id == Quizzes.id)
        .add_columns(Quizzes.id, Quizzes.title, Quizzes.scheduled_date, QuizAttempts.score, QuizAttempts.date_attempted)
        .all()
    )

    return render_template("admin/user_details.html", user=user, quiz_attempts=quiz_attempts)



@admin_bp.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = Users.query.get_or_404(user_id)

    
    QuizAttempts.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    
    flash("User deleted successfully", "success")
    return redirect(url_for("admin_bp.user_management"))


def get_admin_summary_data():
    
    subject_scores = (
        db.session.query(
            Subjects.name.label("subject"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(Chapters, Chapters.subject_id == Subjects.id)
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Subjects.name)
        .all()
    )

    
    chapter_scores = (
        db.session.query(
            Chapters.name.label("chapter"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Chapters.name)
        .all()
    )

    
    quiz_scores = (
        db.session.query(
            Quizzes.title.label("quiz"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Quizzes.title)
        .all()
    )

    
    subject_attempts = (
        db.session.query(
            Subjects.name.label("subject"),
            func.count(QuizAttempts.id).label("attempts"),
        )
        .join(Chapters, Chapters.subject_id == Subjects.id)
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Subjects.name)
        .all()
    )

    return {
        "subject_scores": subject_scores,
        "chapter_scores": chapter_scores,
        "quiz_scores": quiz_scores,
        "subject_attempts": subject_attempts,
    }



def get_admin_summary_data():
    
    subject_scores = (
        db.session.query(
            Subjects.name.label("subject"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(Chapters, Chapters.subject_id == Subjects.id)
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Subjects.name)
        .all()
    )

    
    chapter_scores = (
        db.session.query(
            Chapters.name.label("chapter"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Chapters.name)
        .all()
    )

    
    quiz_scores = (
        db.session.query(
            Quizzes.title.label("quiz"),
            func.avg(QuizAttempts.score).label("avg_score"),
            func.max(QuizAttempts.score).label("top_score"),
        )
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Quizzes.title)
        .all()
    )

    
    subject_attempts = (
        db.session.query(
            Subjects.name.label("subject"),
            func.count(QuizAttempts.id).label("attempts"),
        )
        .join(Chapters, Chapters.subject_id == Subjects.id)
        .join(Quizzes, Quizzes.chapter_id == Chapters.id)
        .join(QuizAttempts, QuizAttempts.quiz_id == Quizzes.id)
        .group_by(Subjects.name)
        .all()
    )

    return {
        "subject_scores": subject_scores,
        "chapter_scores": chapter_scores,
        "quiz_scores": quiz_scores,
        "subject_attempts": subject_attempts,
    }


def generate_admin_charts():
    
    summary_data = get_admin_summary_data()

    def create_base64_bar_chart(data, title, xlabel, ylabel):
        print("Data received for chart:", data)

        
        labels = [row[0] for row in data]
        avg_scores = [row[1] for row in data]
        top_scores = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(10, 5))
        x = range(len(labels))

        ax.bar(x, avg_scores, width=0.4, label="Avg Score", color="blue", align="center")
        ax.bar(x, top_scores, width=0.4, label="Top Score", color="red", align="edge")

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45)
        ax.legend()

        
        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()

    
    subject_chart = create_base64_bar_chart(
        summary_data["subject_scores"],
        title="Average & Top Scores Per Subject",
        xlabel="Subjects",
        ylabel="Scores"
    )

    chapter_chart = create_base64_bar_chart(
        summary_data["chapter_scores"],
        title="Average & Top Scores Per Chapter",
        xlabel="Chapters",
        ylabel="Scores"
    )

    quiz_chart = create_base64_bar_chart(
        summary_data["quiz_scores"],
        title="Average & Top Scores Per Quiz",
        xlabel="Quizzes",
        ylabel="Scores"
    )

    attempts_chart = create_base64_bar_chart(
        summary_data["subject_attempts"],
        title="Subject-Wise Quiz Attempts",
        xlabel="Subjects",
        ylabel="Number of Attempts"
    )

    return subject_chart, chapter_chart, quiz_chart, attempts_chart


@admin_bp.route('/summary')
def admin_summary():
    subject_chart, chapter_chart, quiz_chart, attempts_chart = generate_admin_charts()
    return render_template(
        'admin/summary.html',
        subject_chart=subject_chart,
        chapter_chart=chapter_chart,
        quiz_chart=quiz_chart,
        attempts_chart=attempts_chart
    )
