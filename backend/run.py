from app import create_app
from app.config import Config

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please set OPENROUTER_API_KEY in your .env file")
    exit(1)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5177)
