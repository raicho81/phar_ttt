* The only additional module, which I use is dynaconf for reading settings
    * install it with: python3 -m pip install dynaconf or other suitable way for your distro. I've included requirements.txt too. Check it @ https://www.dynaconf.com/
        [-- $ python3 -m pip freeze > requirements.txt --]
    * Check the README.settings for some program parameters explanation
    * Tested with:
        Python 3.8.10 (default, Sep 28 2021, 16:10:42) [GCC 9.3.0]
    * Run it with:
        [-- $ python3 ttt_main.py --]
    * train_data_3x3.dat is pre-filled with statistics from 10^10 random iterations for board with size 3 and I am using batch traing for the moment
