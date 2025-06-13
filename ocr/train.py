from ai.error_recognition import ErrorRecognizer

def main():
    try:
        print("Starting training...")
        recognizer = ErrorRecognizer()  # This auto-trains if model missing
        print("Training completed!")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
