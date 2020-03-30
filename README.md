# bro-science
Programs towards workout generation and tracking.

This project is set up following the Flask by Example tutorial https://realpython.com/flask-by-example-part-1-project-setup/#project-setup.



This project makes use of Heroku and PostgreSQL to run. Key commands are given below:

    # Creates an application on heroku and use git to set up remote repository
    heroku create <APP-NAME>
    git remote add <REMOTE-NAME> git@heroku.com:<APP-NAME>.git

    # Updates the database on Heroku
    heroku run python manage.py db upgrade --app <APP-NAME>
    
    # Update the environment for the application and print
    heroku config:set APP_SETTINGS=config.<REMOTE-CONFIG> --remote <REMOTE-NAME>
    heroku config --app <APP-NAME>
    
    # Create a database connection on Heroku
    heroku addons:create heroku-postgresql:hobby-dev --app <APP-NAME>
