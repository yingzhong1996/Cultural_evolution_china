from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd, os
from sqlalchemy import func
from dotenv import load_dotenv
load_dotenv() 

app = Flask(__name__)

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost/Chinese_fiction_project'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)
app.jinja_env.globals['attribute'] = getattr

db = SQLAlchemy(app)



class Fiction(db.Model):
    __tablename__ = 'fictions'
    id                        = db.Column(db.Integer, primary_key=True)  # auto-generated
    file_name                 = db.Column(db.String,  nullable=False)
    Score_Romantic_love       = db.Column(db.Float)
    Score_Imagination         = db.Column(db.Float)
    Score_Self_development    = db.Column(db.Float)
    Score_Friendship          = db.Column(db.Float)
    Score_Reciprocal_cooperation = db.Column(db.Float)
    Score_Honor_shame         = db.Column(db.Float)
    Score_Discipline          = db.Column(db.Float)
    Score_Puritanical_morality = db.Column(db.Float)
    Score_Intensive_kinship   = db.Column(db.Float)
    collection                = db.Column(db.String)
    story                     = db.Column(db.String)
    book                      = db.Column(db.String)
    year                      = db.Column(db.Integer)
    tokens                    = db.Column(db.Integer)

def import_csv_to_fictions(csv_path):
    df = pd.read_csv(csv_path)
    # pick only the columns you declared in the model
    want = [
      'file_name',
      # all the Score_* columns
      *[col for col in df.columns if col.startswith('Score_')],
      'collection','story','book','year','tokens'
    ]
    df2 = df[want]
    with app.app_context():
        # recreate table & load
        db.create_all()
        df2.to_sql(
            name='fictions',
            con=db.engine,
            if_exists='append',
            index=False
        )
        print(f"Imported {len(df2)} rows into fictions")



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())



@app.route('/', methods=['GET', 'POST'])
def index():
    msg = None
    if request.method == 'POST':
        user_email = request.form.get('email')
        content = request.form.get('message')
        if content:
            m = Message(email=user_email, content=content)
            db.session.add(m)
            db.session.commit()
            msg = "Your message has been received. Thank you!"
        else:
            msg = "Please enter your message."
    return render_template('index.html', msg=msg)

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/data')
def data():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    q = ( db.session.query(
                func.min(Fiction.id).label('id'),
                Fiction.story,
                Fiction.year
            )
            .group_by(Fiction.story, Fiction.year)
            .order_by(Fiction.year)   # 按年份排序，也可以改成 .order_by(Fiction.story)
        )
    pagination = q.paginate(page=page,
                            per_page=per_page,
                            error_out=False)
    fictions = pagination.items
    return render_template('data.html', items=fictions, pagination=pagination)


@app.route('/detail/<int:fiction_id>')
def detail(fiction_id):
    story_name = Fiction.query.with_entities(Fiction.story) \
                              .filter_by(id=fiction_id) \
                              .scalar()
    fictions = Fiction.query \
                      .filter_by(story=story_name) \
                      .order_by(Fiction.year, Fiction.file_name) \
                      .all()
    return render_template('detail.html',
                           story=story_name,
                           fictions=fictions)




@app.route('/model')
def model():
    return render_template('model.html')


if __name__ == '__main__':
    app.run(debug=True)

