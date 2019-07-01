_git 2>/dev/null

functions[_git_orig]=$functions[_git]

_git_ass() {
  local state
  local line
  _arguments '2: :->command' '*: :->args'

  case $state in
    (command)
      _git_ass_complete
      ;;
    (*)
      _git_ass_complete "${line[@]:1}"
      ;;
  esac
}

_git_ass_complete() {
  local complete=`git ass autocomplete "$@"`
  _arguments $complete
}

_git() {
  local line
  _arguments '*: :->args'

  if [ ${#line} -gt 1 ] && [ "$line[1]" = "ass" ]; then
    _git_ass
  else
    _describe 'command' "('ass:branch enhancer')"
    _git_orig
  fi
}
