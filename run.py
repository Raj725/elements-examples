from api import app

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0')

# SET FLASK_APP=run.py
# SET FLASK_DEBUG=1
# flask run
