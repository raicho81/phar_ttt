  Tic Tac Toe game implementation with self training Monte Carlo algorithm.

* I've implemented a multicore version for training with multiprocessing
* The only additional modules, which I use are dynaconf for reading settings and msgpack for memory usage optimisation.
  Without msgpack even on 4X4 desk the program takes too much memory.
    * install with:
      * bash$ python3 -m pip install dynaconf
      * bash$ python3 -m pip install msgpack,
         or other suitable way for your distro.
      * bash$ python3 -m pip freeze > requirements.txt to freeze rquirements
    * Run it from the project directory with:
        * bash$ python3 ttt/ttt_main.py
    * Check the README.settings for some program parameters explanation
    * Tested with:
        Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
    * train_data_3x3.dat and train_data4x4.dat are pre-filled with statistics from 20*10^6 random iterations for board with size 3 and 4 and I am using batch training for the moment but it can be done incrementally just start the program one more time with more iterations and it should just amend the existing training data. If there is no training data for a given desk state it is just added on the fly with 0 possible outcomes counts (probabilities) when playing and then it starts to get filled with the correct statistics. I must note that I don't use floating point numbers but really just counts and it really doesnt matter if you compare the counts or the counts divided by the total games, which gives the probabilities. There is no difference if you evaluate the inequation 100/100000 < 200/100000  or just 100 < 200 the result is the same but there is no division and no loss of precision and in some cases it can make actually аa difference.
