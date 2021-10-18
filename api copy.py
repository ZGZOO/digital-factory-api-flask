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
	# ref to TodoItem! need to be done
	items = db.relationship(
		'TodoItemModel', 
		backref='todo_note_model', 
		cascade='all, delete, delete-orphan', 
		single_parent=True, 
		lazy='select'
	)

	def __repr__(self):
		return f"Todo Note - {title}"

class TodoItemModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	task = db.Column(db.String(200), nullable=False)
	completed = db.Column(db.Boolean)
	note_id = db.Column(db.Integer, db.ForeignKey('todo_note_model.id'), nullable=False)
	# ref to TodoItem! need to be done

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

	db.session.commit()
	print("Added development dataset")		
app.cli.add_command(seed_data)




def items_list_parser(items):
    if type(items) != list:
        raise ValueError('Expected a list!')

    # Do your validation of the pet objects here. For example:
    for item in items:
        if 'task' not in pet or 'completed' not in pet:
            raise ValueError('Task and if completed is required')

    return items

# need modify; 1 to many
todo_note_parser = reqparse.RequestParser()
todo_note_parser.add_argument('title', type=str, help="Title of the Todo Note is required", required=True)
todo_note_parser.add_argument('items', type=items_list_parser)

# need modify; 1 to many
todo_item_parser = reqparse.RequestParser()
todo_item_parser.add_argument('task', type=str, help="Task name of the Todo Item is required", required=True)
todo_item_parser.add_argument('completed', type=bool, help="Completion status of the Todo Item is required", required=True)


todo_item_fields = {
	'id': fields.Integer,
	'task': fields.String,
	'completed': fields.Boolean,
}


todo_note_fields = {
	'id': fields.Integer,
	'title': fields.String,
	'items': fields.List(fields.Nested(todo_item_fields))
}


# TodoNote route methods
class TodoNote(Resource):
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

	# update an existing Todo Note
	@marshal_with(todo_note_fields)
	def put(self, todo_note_id):
		args = todo_note_parser.parse_args()
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first()
		if not note:
			abort(404, message="Todo Note doesn't exist, cannot update")

		if args['title']:
			note.title = args['title']

		db.session.commit()

		return note, 201

	# delete one Todo Note
	def delete(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first()
		if not note:
			abort(404, message="Todo Note doesn't exist, cannot delete")
		db.session.delete(note)
		db.session.commit()
		return '', 204


	# delete all Todo Notes
	def delete(self):
		db.session.query(TodoNoteModel).delete()
		db.session.commit()
		return '', 204


class TodoItem(Resource):
	# show a list of all Todo Items in a note
	@marshal_with(todo_item_fields)
	def get(self, todo_note_id):
		note = TodoNoteModel.query.filter_by(id=todo_note_id).first()
		print("note is here!!", note)
		items = note.items
		return items, 200


	# create a new Todo Item in a note
	@marshal_with(todo_item_fields)
	def post(self):
		args = todo_item_parser.parse_args()
		item = TodoItemModel(task=args['task'], completed=False)
		db.session.add(item)
		db.session.commit()
		return item, 201


	# update an existing Todo Item in a note
	@marshal_with(todo_item_fields)
	def put(self, todo_item_id):
		args = todo_item_parser.parse_args()
		note = TodoItemModel.query.filter_by(id=todo_note_id).first()
		if not note:
			abort(404, message="Todo Note doesn't exist, cannot update")

		if args['title']:
			note.title = args['title']

		db.session.commit()

		return note, 201


	# delete one Todo Note
	def delete(self, todo_note_id):
		note = TodoItemModel.query.filter_by(id=todo_note_id).first()
		if not note:
			abort(404, message="Todo Note doesn't exist, cannot delete")
		db.session.delete(note)
		db.session.commit()
		return '', 204


	# delete all Todo Notes
	def delete(self):
		db.session.query(TodoItemModel).delete()
		db.session.commit()
		return '', 204

##
## Actually setup the Api resource routing here
##
api.add_resource(TodoNote, '/todos', '/todos/<todo_note_id>')
api.add_resource(TodoItem, '/todos/<todo_note_id>/items')


if __name__ == '__main__':
	app.run(debug=True)




