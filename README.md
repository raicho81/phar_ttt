* Implementation of self training Tic Tac Toe game. The games can be run again itself so it can gather statistics and train this way. When training random moves are done by the two computer "players", which in turn makes the training a monte carlo method.
* The only additional module, which I use is dynaconf for reading settings
    * install it with: python3 -m pip install dynaconf or other suitable way for your distro. I've included requirements.txt too. Check it @ https://www.dynaconf.com/
        [-- $ python3 -m pip freeze > requirements.txt --]
    * Check the README.settings for some program parameters explanation
    * Tested with:
        Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
    * Run it with:
        [-- $ python3 ttt_main.py --]
    * train_data_3x3.dat is pre-filled with statistics from 10^10 random iterations for board with size 3 and I am using batch training for the moment but it can be done incrementally
      just start the program one more time with more iterations and it should just amend the existing training data. If there is no training data for a given desk state it is just added on the fly with 0 possible outcomes counts (probabilities) when playing and then it starts to get filled with the correct statistics. I must note that I don't use floating point numbers but really just counts and it really doesnt matter if you compare the counts or the counts divided by the total games, which gives the probabilities. There is no difference if you evaluate the inequation 100/100000 < 200/100000  or just 100 < 200 the result is the same but there is no division and no loss of precision and in some cases it can make actually аa difference.
