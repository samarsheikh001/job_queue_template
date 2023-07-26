from worker import tasks
from project import create_app, ext_celery
from dotenv import load_dotenv
from flask import jsonify, request
load_dotenv()

app = create_app()
celery = ext_celery.celery


@app.route('/task', methods=['POST'])
def start_task():
    data = request.get_json(force=True)  # Get JSON data from request
    task_name = data.get('task_name')  # Get the task name from the json data

    inputs = data.get('inputs', {})

    task = celery.send_task(task_name, kwargs=inputs)
    return jsonify({'task_id': task.id}), 202


@app.route('/task/<task_id>', methods=['GET'])
def get_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.result is None:
        return jsonify({'task_status': 'PENDING', 'task_result': 'Task does not exist'}), 200
    elif task.status == 'SUCCESS':
        result = task.get()  # This will also remove the task result
        return jsonify({'task_status': task.status, 'task_result': result}), 200
    elif task.status == 'PENDING' or task.status == 'STARTED':
        return jsonify({'task_status': task.status, 'task_result': 'Task is still processing'}), 200
    else:
        task.forget()  # This will remove the task result
        return jsonify({'task_status': task.status, 'task_result': 'Task failed or unknown'}), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()  # get the incoming JSON structure
    # do something with the data here, like print it to console:
    print(data)
    # return a response
    return jsonify({'response': 'Webhook received'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')
