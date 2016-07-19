# tab completion for jinkies
# put this in ~/.bash_completion.d/
# it caches jobs and views once per shell session

_getjobs() {
    jinkies list jobs
}

_getviews() {
    jinkies list views |cut -d':' -f1 |grep -v All
}

_jinkies_complete() {
    local cur
    # cache the jobs and views list for this shell session
    if [ -z "$_jinkies_complete_jobs" ]; then
        _jinkies_complete_jobs=$(_getjobs)
    fi
    if [ -z "$_jinkies_complete_views" ]; then
        _jinkies_complete_views=$(_getviews)
    fi

    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}
    case "$prev" in
        jinkies)
            COMPREPLY=($(compgen -W "list show view build" -- $cur))
            return 0
            ;;
        show)
            COMPREPLY=($(compgen -W "${_jinkies_complete_views}" -- $cur))
            return 0
            ;;
        build|view|params)
            COMPREPLY=($(compgen -W "${_jinkies_complete_jobs}" -- $cur))
            return 0
            ;;
    esac

    # completing an option
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "-h --help --version --config" -- $cur))
    fi
}

complete -F _jinkies_complete "jinkies"
