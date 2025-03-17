# Text Translation Service

A service that helps translate books or texts by sending small portions to users daily via email or SMS, collecting their translations, and assembling them into complete translated documents.

## Features

- Parse books/texts and divide them into daily portions
- Send text portions to users via email or SMS
- Receive and process translated responses
- Assemble translations into complete documents
- Support multiple users and multiple translation projects
- Track progress for each user and text

## Project Structure

- `app.py`: Main application entry point
- `text_manager.py`: Handles text parsing and segmentation
- `user_manager.py`: Manages user information and progress
- `messaging.py`: Handles sending emails/SMS and receiving responses
- `translation_assembler.py`: Compiles translations into final documents
- `models.py`: Data models for the application
- `config.py`: Configuration settings

## Usage

1. Register a text for translation
2. Add users and assign them to texts
3. Start the service to send daily portions
4. Translations are assembled as responses are received

## Requirements

- Python 3.8+
- Additional libraries (see requirements.txt)
