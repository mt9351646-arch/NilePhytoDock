from scientific import pockets
from scientific.runtime import p2rank_args
from tools.validate_paths import main
base=p2rank_args()
pockets.p2rank_args=lambda:[base[0],'-Dfile.encoding=UTF-8','-Dsun.jnu.encoding=UTF-8',*base[1:]]
main()
