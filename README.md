  Tic Tac Toe game implementation with self training Monte Carlo algorithm.

* I didn't test if it is playable as I was busy with the Redis -> Postgres stuff. The db_dump is out of date currently, but the schema is ok and there is docker-compose.yml, which should make you running in no time :)
* I am using git LFS in this repo so you may need to install/initialize git LFS
* I've implemented (finally) ingesting of the training data in Postgres instead of using RAM and dumping the training data in files.
* I've implemented a multicore version for training with multiprocessing and multi-threading and Postgres connection pooling (well a little bit rudimentary) and also now ingesting training data from multiple machines running the program should be OK. 
* I've implemented some Redis front-end to cache data before ingesting it in Postgres to reduce the DB quieries. Probably still buggy but already working :)
* I've optimised some DB stuff with Stored Procedures and Functions in SQL and pl/pgSQL
* install with:
  * bash$ python3 -m pip install dynaconf
  * bash$ python3 -m pip install msgpack
  * bash$ python3 -m pip install psycopg2
  * bash$ python3 -m pip install redis
  * bash$ python3 -m pip install pottery,
     or other suitable way for your distro.
  * bash$ python3 -m pip freeze > requirements.txt to freeze rquirements
* Run it from the project directory with:
    * bash$ python3 ttt/ttt_main.py
* Check the README.settings for some program parameters explanation (currently out of date)
* Tested with:
    Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
* SQL/schema.sql - Contains DB stucture with no training data. dump.pg_dump is out of date.
