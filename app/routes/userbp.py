from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.models import Quizzes, Questions, QuizAttempts, Options, db, Subjects, Chapters
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    search_query = request.args.get('search', '').strip().lower()
    date_filter = request.args.get('date')
    today = datetime.today().date()

    quizzes = Quizzes.query.filter(Quizzes.scheduled_date >= today)

    if search_query:
        quizzes = quizzes.filter(Quizzes.title.ilike(f"%{search_query}%"))

    if date_filter:
        try:
            search_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            quizzes = quizzes.filter(Quizzes.scheduled_date == search_date)
        except ValueError:
            pass

    quizzes = quizzes.all()

    for quiz in quizzes:
        quiz.num_questions = Questions.query.filter_by(quiz_id=quiz.id).count()

    return render_template('user/dashboard.html', user=current_user, quizzes=quizzes)



@user_bp.route('/quiz/view/<int:quiz_id>', methods=['GET'])
@login_required
def view_quiz(quiz_id):
    quiz = Quizzes.query.get_or_404(quiz_id)
    total_questions = Questions.query.filter_by(quiz_id=quiz_id).count()
    return render_template('user/quiz_details.html', quiz=quiz, total_questions=total_questions)



@user_bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quizzes.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)

    if not questions:
        flash("No questions available for this quiz.", "danger")
        return redirect(url_for('user_bp.user_dashboard'))

    if 'quiz_id' not in session or session['quiz_id'] != quiz_id:
        session['quiz_id'] = quiz_id
        session['quiz_progress'] = 0
        session['selected_answers'] = {}
        session['quiz_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    current_question_index = int(request.form.get("current_question", session['quiz_progress']))

    try:
        quiz_duration = quiz.duration
        hours, minutes = (0, int(quiz_duration)) if ":" not in quiz_duration else map(int, quiz_duration.split(":"))
        quiz_start_time = datetime.strptime(session['quiz_start_time'], '%Y-%m-%d %H:%M:%S')
        quiz_end_time = quiz_start_time + timedelta(hours=hours, minutes=minutes)
    except (ValueError, AttributeError):
        flash("Invalid quiz duration format!", "danger")
        return redirect(url_for('user_bp.user_dashboard'))

    if datetime.now() > quiz_end_time:
        flash("Time is up! Your quiz has been auto-submitted.", "danger")
        return redirect(url_for('user_bp.submit_quiz', quiz_id=quiz_id))

    if request.method == 'POST':
        selected_option = request.form.get('option')
        if selected_option:
            session['selected_answers'][str(current_question_index)] = int(selected_option)

        if 'next' in request.form and current_question_index < total_questions - 1:
            session['quiz_progress'] = current_question_index + 1
        elif 'previous' in request.form and current_question_index > 0:
            session['quiz_progress'] = current_question_index - 1
        elif 'submit' in request.form:
            return redirect(url_for('user_bp.submit_quiz', quiz_id=quiz_id))

    question = questions[session['quiz_progress']]
    options = Options.query.filter_by(question_id=question.id).all()

    return render_template(
        'user/quiz_interface.html', 
        quiz=quiz, 
        question=question, 
        options=options, 
        total_questions=total_questions, 
        current_question_index=session['quiz_progress'],  
        quiz_end_time=quiz_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        selected_answers=session['selected_answers']
    )



@user_bp.route('/submit_quiz/<int:quiz_id>', methods=['GET'])
@login_required
def submit_quiz(quiz_id):
    if 'selected_answers' not in session or session.get('quiz_id') != quiz_id:
        return redirect(url_for('user_bp.user_dashboard'))

    total_score = 0
    quiz = Quizzes.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    for index, question in enumerate(questions):
        correct_option = Options.query.filter_by(question_id=question.id, is_correct=True).first()
        user_answer = session['selected_answers'].get(str(index))  

        if user_answer is not None and correct_option and user_answer == correct_option.id:
            total_score += 1

    attempt = QuizAttempts(user_id=current_user.id, quiz_id=quiz_id, score=total_score, date_attempted=datetime.now())
    db.session.add(attempt)
    db.session.commit()

    session.pop('quiz_progress', None)
    session.pop('selected_answers', None)
    session.pop('quiz_id', None)
    session.pop('quiz_start_time', None)

    flash(f"Quiz submitted! Your score: {total_score}/{len(questions)}", "success")
    return redirect(url_for('user_bp.quiz_scores'))



@user_bp.route('/quiz_scores', methods=['GET'])
@login_required
def quiz_scores():
    search_query = request.args.get("search", "").strip().lower()

    attempts = (
        db.session.query(QuizAttempts, Quizzes)
        .join(Quizzes, QuizAttempts.quiz_id == Quizzes.id)
        .filter(QuizAttempts.user_id == current_user.id)
        .order_by(QuizAttempts.date_attempted.desc())
        .all()
    )

    if search_query:
        attempts = [
            (attempt, quiz)
            for attempt, quiz in attempts
            if search_query in quiz.title.lower() or search_query in str(attempt.date_attempted)
        ]

    return render_template('user/quiz_scores.html', attempts=attempts)



def generate_subject_chart():
    
    user_attempts = (
        db.session.query(QuizAttempts, Quizzes, Chapters, Subjects)
        .join(Quizzes, QuizAttempts.quiz_id == Quizzes.id)
        .join(Chapters, Quizzes.chapter_id == Chapters.id)  
        .join(Subjects, Chapters.subject_id == Subjects.id)  
        .filter(QuizAttempts.user_id == current_user.id)
        .all()
    )

    print("🔍 User Attempts Retrieved:", user_attempts)  

    if not user_attempts:
        print("🚨 No quiz attempts found for user:", current_user.id)
        return None  

   
    subject_scores = {}
    for attempt, quiz, chapter, subject in user_attempts:
        if subject.name not in subject_scores:
            subject_scores[subject.name] = []
        subject_scores[subject.name].append(attempt.score)

        print("📊 Processed Subject Scores:", subject_scores)  


   
    subject_names = list(subject_scores.keys())
    avg_scores = [round(sum(scores) / len(scores), 2) for scores in subject_scores.values()]
    

   
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(subject_names, avg_scores, color='purple')
    ax.set_xlabel("Subjects")
    ax.set_ylabel("Average Score")
    ax.set_title("Average Score by Subject")
    ax.set_xticklabels(subject_names, rotation=45)

    
    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()


@user_bp.route('/summary')
@login_required
def summary():
    subject_chart = generate_subject_chart()
    return render_template('user/summary.html', subject_chart=subject_chart)
