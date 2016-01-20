#!/bin/sh

python -c 'import docopt'

if [ $? != 0 ]; then
    echo "Missing docopt module."
    echo "  pip install docopt"
    echo ""
    echo "or for ubuntu/debian users:"
    echo "  apt-get install python-docopt"
fi

cp jinkies.bash "$HOME/.bash_completion.d/"
cp jinkies.py "$HOME/.local/bin/jinkies"
chmod a+x "$HOME/.local/bin/jinkies"

echo $PATH | grep "$HOME/.local/bin" > /dev/null

if [ $? != 0 ]; then
    echo "Installed jinkies into ~/.local/bin/ which is not in your PATH:"
    echo "  export \$PATH=\$PATH:$HOME/.local/bin"
else
    echo "Installed jinkies into ~/.local/bin/\n"
fi

python -c 'import jinkies; print jinkies.url_help'
