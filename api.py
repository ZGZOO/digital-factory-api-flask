from flask import Flask
import click
from flask.cli import with_appcontext
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
# Suppress deprecation warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class TodoNoteModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	items = db.relationship('TodoItemModel', backref='todo_note_model', cascade="all, delete-orphan", lazy='joined')

	# items here too?
	def __repr__(self):
		return f"Todo Note - {title}"


class TodoItemModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	task = db.Column(db.String(200), nullable=False)
	completed = db.Column(db.Boolean, default=False)
	note_id = db.Column(db.Integer, db.ForeignKey('todo_note_model.id'), nullable=False)

	# note_id here too?
	def __repr__(self):
		return f"Todo Item - {task} - {completed}"


@click.command(name="init_db")
@with_appcontext
def init_db():
	# Drops and Creates fresh database
	db.drop_all()
	db.create_all()
	print("Initialized fresh new DB")
app.cli.add_command(init_db)


@click.command(name="seed_data")
@with_appcontext
def seed_data():
	db.drop_all()
	db.create_all()

	note1 = TodoNoteModel(
		title="Get in Digital Factory")
	task1 = TodoItemModel(
		task="Initial interview with Victor",
		completed=True)
	task2 = TodoItemModel(
		task="Do code challenge",
		completed=True)
	task3 = TodoItemModel(
		task="Final interview",
		completed=False)
	task4 = TodoItemModel(
		task="Final decision",
		completed=False)
	db.session.add(task1)
	db.session.add(task2)
	db.session.add(task3)
	db.session.add(task4)

	task1.todo_note_model = note1
	task2.todo_note_model = note1
	task3.todo_note_model = note1
	task4.todo_note_model = note1
	db.session.add(note1)


	note2 = TodoNoteModel(
		title="Work Out")
	task5 = TodoItemModel(
		task="Initial interview with Victor",
		completed=True)
	task6 = TodoItemModel(
		task="Do code challenge",
		completed=True)
	db.session.add(task5)
	db.session.add(task6)

	task5.todo_note_model = note2
	task6.todo_note_model = note2
	db.session.add(note2)

	db.session.commit()
	print("Added development dataset")		
app.cli.add_command(seed_data)



todo_note_parser = reqparse.RequestParser()
todo_note_parser.add_argument('title', type=str, help="Title of the Todo Note is required", required=True)


todo_item_parser = reqparse.RequestParser()
todo_item_parser.add_argument('task',type=str, help="Task of the Todo Item is required", required=True)
todo_item_parser.add_argument('completed',type=bool, help="Boolean of the Todo Item is required", required=True)


todo_item_put_parser = reqparse.RequestParser()
todo_item_put_parser.add_argument('task',type=str, help="Task of the Todo Item")
todo_item_put_parser.add_argument('completed', default=False, type=lambda v: v.lower() == 'true', help="Boolean of the Todo Item")



todo_item_fields = {
	'id': fields.Integer,
	'task': fields.String,
	'completed': fields.Boolean
}


todo_note_fields = {
	'id': fields.Integer,
	'title': fields.String,
	'items': fields.List(fields.Nested(todo_item_fields))
}


# TodoNotes route methods
class TodoNotes(Resource):
	# show a list of all Todo Notes
	@marshal_with(todo_note_fields)
	def get(self):
		notes = TodoNoteModel.query.all()
		return notes, 200


	# create a new Todo Note
	@marshal_with(todo_note_fields)
	def post(self):
		args = todo_note_parser.parse_args()
		note = TodoNoteModel(title=args['title'])
		db.session.add(note)
		db.session.commit()
		return note, 201


	# delete all Todo Notes
	def delete(self):
		db.session.query(TodoNoteModel).delete()
		db.session.commit()
		return '', 204


class TodoNote(Resource):
	# show a specific Todo Note based on id
	@marshal_with(todo_note_fields)
	def get(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		return note, 200


	# update a specific Todo Note based on id
	@marshal_with(todo_note_fields)
	def put(self, todo_note_id):
		args = todo_note_parser.parse_args()
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		if args['title']:
			note.title = args['title']
		db.session.commit()
		return note, 201


	# delete one Todo Note
	def delete(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		db.session.delete(note)
		db.session.commit()
		return '', 204


class TodoNoteCompleted(Resource):
	# make all the items as completed for a note
	@marshal_with(todo_note_fields)
	def put(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		items = note.items
		for item in items:
			item.completed = True
		db.session.commit()
		return note, 201


class TodoItems(Resource):
	# show the list of all the Todo Items of a specific note based on note_id
	@marshal_with(todo_item_fields)
	def get(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		items = note.items
		return items, 200


	# create a new Todo Item for a specific note based on note_id
	# with field "completed" a default "False"
	@marshal_with(todo_item_fields)
	def post(self, todo_note_id):
		args = todo_item_parser.parse_args()
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		items = note.items
		item = TodoItemModel(task=args['task'], completed=False)
		items.append(item)
		db.session.commit()
		return item, 201


	# delete all Todo Items of a specific note based on note_id
	def delete(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first_or_404(description='Todo Note with id={} is not available'.format(todo_note_id))
		items = note.items
		items.delete()
		db.session.commit()
		return '', 204


class TodoItem(Resource):
	# show a specific Todo Item based on item_id of a note
	@marshal_with(todo_item_fields)
	# don't need todo_note_id???
	def get(self, todo_item_id):
		item = TodoItemModel.query.filter_by(id=todo_item_id).first_or_404(description='Todo Item with id={} is not available'.format(todo_item_id))
		return item, 200


	# update a specific Todo Item based on item_id of a note
	# can also update a Todo Item to be completed
	@marshal_with(todo_item_fields)
	# don't need todo_note_id???
	def put(self, todo_item_id):
		args = todo_item_put_parser.parse_args()
		item = TodoItemModel.query.filter_by(id=todo_item_id).first_or_404(description='Todo Item with id={} is not available'.format(todo_item_id))
		if args['task']:
			item.task = args['task']
		item.completed = args['completed']
		db.session.commit()
		return item, 201


	# delete one Todo Note
	def delete(self, todo_item_id):
		item = TodoItemModel.query.filter_by(id=todo_item_id).first_or_404(description='Todo Item with id={} is not available'.format(todo_item_id))
		db.session.delete(item)
		db.session.commit()
		return '', 204


##
## Actually setup the Api resource routing here
##
api.add_resource(TodoItem, '/todos/items/<int:todo_item_id>')
api.add_resource(TodoItems, '/todos/<int:todo_note_id>/items')
api.add_resource(TodoNoteCompleted, '/todos/<int:todo_note_id>/completed')
api.add_resource(TodoNote, '/todos/<int:todo_note_id>')
api.add_resource(TodoNotes, '/todos')



if __name__ == '__main__':
	app.run(debug=True)




