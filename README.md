* Tic Tac Toe game implementation with self training Monte Carlo algorithm.
* I've implemented a kind of master/slave strategy. Slaves are publishing to Redis and the Master is updating the data to the DB when more statistics is gathered for given states (well, 2 or more samples for now per state before the state goes to the DB). I am using Redis streams to post the updates from the slaves to the master(s). Multiple Masters can work simultaniously provided that they are identified as different stream group consumers in Redis.
* I've implemented batch updates of the states coming from Redis to the DB first with my own Stored Procedures in pl/PgSQL and then with Django ORM. Well the performance is the same.
* The db_dump is out of date currently, but the schema is ok and there is docker-compose.yml, which should make you running in no time :) Also now I have Django ORM DB model so you can can initialize the DB this way too.
* I am using git LFS in this repo so you may need to install/initialize git LFS
* I've implemented a multicore version for training with multiprocessing and multi-threading and Postgres connection pooling (well a little bit rudimentary) and also now ingesting training data from multiple machines running the program should be OK. 
* I've implemented some Redis front-end to cache data before ingesting it in Postgres to reduce the DB quieries.
* install with:
* * bash$ pyton3 -m venv venv
* * bash$ source venv/bin/activate
  * bash$ python3 -m pip install dynaconf
  * bash$ python3 -m pip install msgpack
  * bash$ python3 -m pip install psycopg2 (python3 -m pip install psycopg2-binary if you don't wan't to enter all the hustle ...)
  * bash$ python3 -m pip install redis
  * bash$ python3 -m pip install pottery
  * bash$ python3 -m pip install django
  * bash$ python3 -m pip freeze > requirements.txt to freeze rquirements
* Run it from the project directory with:
    * bash$ python3 ttt/ttt_main.py
* Check the README.settings for some program parameters explanation (currently out of date)
* Tested with:
    Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
* SQL/schema.sql - Contains DB stucture with no training data.
