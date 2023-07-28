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
    queue = data.get('queue')  # Get the task name from the json data

    inputs = data.get('inputs', {})

    task = celery.send_task(task_name, kwargs=inputs,
                            queue=f"{queue}_{task_name}")
    return jsonify({'task_id': task.id}), 202


@app.route('/task/<task_id>', methods=['GET'])
def get_status(task_id):
    try:
        task = celery.AsyncResult(task_id)
        return jsonify({'task_status': task.status, 'task_result': task.result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()  # get the incoming JSON structure
    # do something with the data here, like print it to console:
    print(data)
    # return a response
    return jsonify({'response': 'Webhook received'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')
