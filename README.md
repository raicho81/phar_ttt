  Tic Tac Toe game implementation with self training Monte Carlo algorithm.

* I am using git LFS in this repo so you may need to install/initialize git LFS
* I've implemented (finally) ingesting of the training data in Postgres instead of using RAM and dumping the training data in files.
* I've implemented a multicore version for training with multiprocessing and also now ingesting training data from multiple machines running the program should be OK. I had some *really* bad time trying to implement the the multicore version wih Processes isntead of threads.
* install with:
  * bash$ python3 -m pip install numpy
  * bash$ python3 -m pip install dynaconf
  * bash$ python3 -m pip install msgpack
  * bash$ python3 -m pip install psycopg2,
     or other suitable way for your distro.
  * bash$ python3 -m pip freeze > requirements.txt to freeze rquirements
* Run it from the project directory with:
    * bash$ python3 ttt/ttt_main.py
* Check the README.settings for some program parameters explanation
* Tested with:
    Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
* postgres.sql - Contains DB stucture no training data
