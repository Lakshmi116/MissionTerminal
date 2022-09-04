from tracemalloc import start


round = 7
round = int(input("Round: "))
start = int(input("Start: "))
use = int(input("Use: "))
# use = 3



def mp(begin, use, round):
    if(use>=begin):
        return round
    return (begin-use)*0.75 + round 


for i in range(20):
    next = mp(start, use, round)
    print(i+1, next)
    start = next

    