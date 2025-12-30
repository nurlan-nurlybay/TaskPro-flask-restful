from app import create_app

# Instantiate the app using the factory
app = create_app()

if __name__ == "__main__":
    # We use debug=True for development to get hot-reloading
    app.run(debug=True)
