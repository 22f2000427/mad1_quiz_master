from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime

from models.models import Users, Subjects, Chapters, Quizzes, Questions, Options, db
from routes.login import login_bp
from routes.userbp import user_bp
from routes.adminbp import admin_bp

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"

db.init_app(app)

with app.app_context():
    db.create_all()

    
    if not Users.query.first():
        admin_user = Users(username="admin", password_hash=generate_password_hash("adminpass"), role="admin", email="admin@example.com" , full_name = "Admin" , dob = datetime.strptime("1995-06-15", "%Y-%m-%d").date() , qualification = "student")
        user1 = Users(username="user1", password_hash=generate_password_hash("password1"), role="user", email="user1@example.com" , full_name = "User1", dob =datetime.strptime("1995-06-15", "%Y-%m-%d").date() , qualification = "student")
        user2 = Users(username="user2", password_hash=generate_password_hash("password2"), role="user", email="user2@example.com" , full_name = "User2" , dob = datetime.strptime("1995-06-15", "%Y-%m-%d").date() , qualification = "admin" )
        
        db.session.add_all([admin_user, user1, user2])
        db.session.commit()
        print(" Sample users added.")

    
    subjects_data = ["Mathematics", "Physics", "Chemistry", "Computer Science"]
    for name in subjects_data:
        if not Subjects.query.filter_by(name=name).first():
            db.session.add(Subjects(name=name))
    
    db.session.commit()
    print(" Subjects added.")

    
    admin_user = Users.query.filter_by(username="admin").first()
    for subject in Subjects.query.all():
        for i in range(1, 4):  # 3 Chapters per Subject
            chapter_name = f"Chapter {i} - {subject.name}"
            chapter = Chapters.query.filter_by(name=chapter_name, subject_id=subject.id).first()
            if not chapter:
                chapter = Chapters(name=chapter_name, subject_id=subject.id)
                db.session.add(chapter)
        
        db.session.commit()

        for chapter in Chapters.query.filter_by(subject_id=subject.id).all():
            for j in range(1, 3):  # 2 Quizzes per Chapter
                quiz_title = f"Quiz {j} - {chapter.name}"
                quiz = Quizzes.query.filter(Quizzes.title==quiz_title, Quizzes.chapter_id==chapter.id).first()
                if not quiz:
                    quiz = Quizzes(
                        title=quiz_title, chapter_id=chapter.id,
                        scheduled_date=datetime(2025, 3, 30), duration=10, creator_id=admin_user.id
                    )
                    db.session.add(quiz)
            
            db.session.commit()

           
            question_bank = {
                "Mathematics": [
                    ("What is 2 + 2?", ["3", "4", "5", "6"], 1),
                    ("Solve for x: 3x = 12", ["x = 2", "x = 3", "x = 4", "x = 5"], 2),
                    ("What is the square root of 16?", ["2", "3", "4", "5"], 2),
                    ("What is 5 * 6?", ["28", "30", "32", "34"], 1),
                    ("What is the derivative of x^2?", ["x", "2x", "x^2", "1"], 1),
                ],
                "Physics": [
                    ("What is the speed of light?", ["300,000 km/s", "150,000 km/s", "450,000 km/s", "500,000 km/s"], 0),
                    ("What is Newton's second law?", ["F=ma", "E=mc^2", "V=IR", "P=mv"], 0),
                    ("What is the unit of force?", ["Newton", "Joule", "Pascal", "Watt"], 0),
                    ("What is the first law of thermodynamics?", ["Conservation of energy", "Entropy always increases", "Force equals mass times acceleration", "Energy equals mass times speed of light squared"], 0),
                    ("Which planet has the strongest gravity?", ["Mars", "Earth", "Jupiter", "Venus"], 2),
                ],
                "Chemistry": [
                    ("What is the chemical formula for water?", ["H2O", "CO2", "O2", "NaCl"], 0),
                    ("What is the atomic number of carbon?", ["6", "12", "14", "16"], 0),
                    ("Which gas do plants use for photosynthesis?", ["Oxygen", "Carbon Dioxide", "Hydrogen", "Nitrogen"], 1),
                    ("What is the pH of pure water?", ["5", "6", "7", "8"], 2),
                    ("What is the most abundant gas in Earth's atmosphere?", ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"], 2),
                ],
                "Computer Science": [
                    ("What does CPU stand for?", ["Central Processing Unit", "Computer Personal Unit", "Central Process Utility", "Core Processing Unit"], 0),
                    ("What is the full form of RAM?", ["Random Access Memory", "Read Access Memory", "Real Allocated Memory", "Run Access Mode"], 0),
                    ("What is the binary representation of 10?", ["1010", "1001", "1100", "1111"], 0),
                    ("Which language is primarily used for web development?", ["Python", "Java", "HTML", "C++"], 2),
                    ("What is an IP address?", ["A computer's unique ID", "A type of software", "An operating system", "A virus"], 0),
                ],
            }

            for quiz in Quizzes.query.filter(Quizzes.chapter_id==chapter.id).all():
                selected_questions = question_bank.get(subject.name, [])[:5]  # Get exactly 5 questions
                for q_text, options, correct_index in selected_questions:
                    question = Questions.query.filter_by(quiz_id=quiz.id, text=q_text).first()
                    if not question:
                        question = Questions(quiz_id=quiz.id, text=q_text)
                        db.session.add(question)
                        db.session.commit()

                        for idx, option_text in enumerate(options):
                            option = Options(question_id=question.id, text=option_text, is_correct=(idx == correct_index))
                            db.session.add(option)

                db.session.commit()

    print("✅ Chapters, quizzes, questions, and options added.")


app.register_blueprint(login_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_bp.login"

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def main():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True)

