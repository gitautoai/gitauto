# Jira Webhook Setup Instructions

## Overview
This document provides instructions on how to set up a Jira webhook to integrate with our system.

## Steps to Set Up Jira Webhook

1. **Create a Webhook in Jira**
   - Navigate to Jira settings and select 'System'.
   - Under 'Advanced', select 'Webhooks'.
   - Click 'Create a Webhook'.
   - Enter a name for the webhook.
   - Set the URL to `http://<your-server-ip>:5000/jira-webhook`.
   - Select the events you want to trigger the webhook, such as 'Issue Created'.
   - Save the webhook.

2. **Configure the Webhook Listener**
   - Update the `services/jira_webhook_config.py` file with your authentication details if required.

3. **Run the Webhook Listener**
   - Start the Flask application by running `python services/jira_webhook_listener.py`.

## Testing
Ensure that the webhook is correctly triggered by creating a new ticket in Jira and checking the logs of the webhook listener service.