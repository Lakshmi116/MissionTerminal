import math


# rnd = 7
# rnd = int(input("Round: "))
# # # start = int(input("Start: "))
# use = int(input("Use: "))
# # use = 3



def mp(begin, use, rnd):
    if(use>=begin):
        return rnd
    return (begin-use)*0.75 + rnd 
# start = []
# for i in range(10):
#     start.append(i+1)
# for i in range(10):
#     for st in range(len(start)):
#         next = mp(start[st], use, rnd)
#         k = round(next, 1)
#         print(k, end=" ")
#         start[st] = next
#     print()

# out = open("new.csv", "w")

# for rnd in range(5,10):
#     for use in range(rnd+1):
#         start = []
#         for i in range(21):
#             start.append(i+1)
#         for i in range(10):
#             for st in range(len(start)):
#                     next = mp(start[st], use, rnd)
#                     k = round(next, 1)
#                     tmp = str(i) + ", "+str(rnd)+", "+str(use)+", "+str(st)+", "+str(k)+"\n"
#                     out.write(tmp)
#                     out.write("")
#                     start[st] = next 


rnd = int(input("Round: "))
start = int(input("start: "))

cnt = 0
while(True):
    use = int(input("uise: "))
    next = mp(start, use, rnd)
    cnt+=1
    print(cnt, next)
    start = next

    