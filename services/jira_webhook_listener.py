from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    data = request.json
    # Process the incoming data from Jira
    # For example, extract ticket information and log it
    ticket_info = data.get('issue', {})
    print(f"Received new ticket: {ticket_info}")
    # Convert the data into a format that our system can process
    # TODO: Implement the conversion logic
    return jsonify({'status': 'success'}), 200

if __name__ == "__main__":
    app.run(port=5000)