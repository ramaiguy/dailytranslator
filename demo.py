#!/usr/bin/env python3
"""
Demo script for the Text Translation Service.

This script demonstrates the basic workflow of the translation service:
1. Registering a text
2. Registering a user
3. Assigning a text to a user
4. Sending daily portions
5. Processing a sample reply
6. Generating a translation file
"""

from app import TranslationServiceApp
from models import DeliveryMethod

# Initialize the application
app = TranslationServiceApp()

# 1. Register our example text
print("Registering example text...")
text = app.register_text(
    file_path="example.txt",
    title="Example Short Text",
    author="Demo Author",
    language="en",
    target_language="es",
    sentences_per_day=2
)
print(f"Registered text: {text.title} (ID: {text.id})")
print(f"Total sentences: {len(text.sentences)}")
print()

# 2. Register a test user
print("Registering test user...")
user = app.register_user(
    name="Test User",
    email="test@example.com",
    preferred_method=DeliveryMethod.EMAIL
)
print(f"Registered user: {user.name} (ID: {user.id})")
print()

# 3. Assign the text to the user
print("Assigning text to user...")
app.assign_text_to_user(user.id, text.id)
print()

# 4. Send daily portions
print("Sending daily portions...")
app.send_daily_portions([user.id])
print()

# 5. Simulate receiving a reply with translations
print("Processing a sample translation reply...")
sample_reply = """
[1] El rápido zorro marrón salta sobre el perro perezoso.
[2] Este es un archivo de texto simple que podemos usar para probar nuestro servicio de traducción.
"""
app.process_translation_reply(
    sender="test@example.com",
    subject=f"Daily Translation: {text.title}",
    body=sample_reply
)
print()

# 6. Generate a translation file
print("Generating translation file...")
output_file = app.generate_translation_file(text.id, "txt")
print()

print("Demo completed!")
print("The translation service workflow has been demonstrated.")
print("The example text has been partially translated and a translation file generated.")
