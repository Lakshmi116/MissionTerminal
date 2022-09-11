from argparse import SUPPRESS
from dataclasses import replace
from dis import dis
# from distutils.spawn import spawn
from collections.abc import Iterable
import queue
from socket import getnameinfo
from typing import Tuple
from unittest import removeResult
import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

"""
    TODO
    ----
    1. (done) Adaptive building correction +
    2. (done) Replacement logic + 
    3. (done) LOC logic
    4. (done) Left or Right Damage ease? Next time decision helper flags +
    5.        Bandit from right 
    6. (done) Demolisher + Interceptor + 
    7. (done) Is left weak? Throw the demolishers
    8. (doing......) Scout correction + 
    9.        Heavy attack at border strategy
    10.       Sense danger at the mouth + 
    11.(done) Expensive bandit 
    12.       Overload the build queues + 
    13.(done) Save interceptors (spl case: Enemy mobile points just less than 3 multiple, not probable attack)
    14.       Tune all the thresholds
    15.       Save enemy state ++
    16.(done) Timing algorithms 
    17.(done) Tail is not resisting demolisher + scouts ++
"""

class Maze():
    def __init__(self):
        self.left_corner_walls = [[0,14], [1,14]]
        self.left_corner_locations = [[0,14], [1,14],[2,14], [3,14], [1,15], [2,15], [3,15]]
        self.left_corner_locations_big = [[4, 18], [3, 17], [4, 17], [2, 16], [3, 16], [4, 16],\
                                          [1, 15], [2, 15], [3, 15], [4, 15], [0, 14],\
                                          [1, 14], [2, 14], [3, 14], [4, 14]]
        pass 

    def cornerStrength(self, game_state, forBandit = True):
        """usage: returns the left corner's health and damage"""
        # Idea: Initial scouts = 6*(health of corners walls/120) + 2*u_turrets + 1*n_turrets (percentage upgraded_turrets)- 0.8*(tur_damage)
        # Remaining scouts >= 6
        # 
        hurdle_strength = 0.4
        wall_strength = 0
        wall_den = 0
        hurdle_walls = self.left_corner_walls
        all_locs = self.left_corner_locations

        if(forBandit == False):
            all_locs = self.left_corner_locations_big


        for loc in hurdle_walls:
            unit = game_state.contains_stationary_unit(loc)
            if(unit == False):
                continue
            wall_strength += unit.health
            wall_den += unit.max_health
        if(wall_den!=0):
            hurdle_strength = wall_strength/wall_den
        u_turrets = 0
        n_turrets = 0
        tur_damage = 0
        for loc in all_locs:
            unit = game_state.contains_stationary_unit(loc)
            if(unit == False):
                continue
            if(unit.unit_type == TURRET):
                if(unit.upgraded):
                    u_turrets += 1
                elif(loc!=[3,15]):
                    n_turrets += 1
                tur_damage += unit.health/unit.max_health
        
        return [hurdle_strength, u_turrets, n_turrets, tur_damage]

    def weakSide(self, game_state):
        """Usage: returns the weak side of the enemy map"""
        # Idea: left, right corners turret + wall count
        left_pts = 0
        right_pts = 0
        for loc in self.left_corner_locations_big:
            r = [27-loc[0],loc[1]]
            unit_l = game_state.contains_stationary_unit(loc)
            unit_r = game_state.contains_stationary_unit(r)
            if(unit_l != False):
                left_pts+=unit_l.health
            if(unit_r!=False):
                right_pts+=unit_r.health
        return left_pts<right_pts 

    def turretAtOpening(self, game_state):
        """returns self.openings turret health and damage (enemy)"""
        pass


class Bunker():
    def __init__(self):
        # seed = random.randrange(maxsize)
        # random.seed(seed)
        # Current wall locations
        self.bandit_walls = [[0, 13], [1, 13],[2, 13], [3, 13]]
        self.top_right_walls = [[26, 13], [27, 13]]
        self.right_walls = [[25, 11], [24, 10], [23, 9], [22, 8], [21, 7], [20, 6]]
        self.bottom_walls = [[12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 5], [18, 6], [19, 6]]
        self.left_walls = [ [8, 9], [9, 8], [10, 7], [11, 6],[6, 11], [7, 10],[5,12]]
        self.loc_walls = [[5,12]]

        # Current Turret Locations (!!Remove!!)
        self.prime_turrets = [[2, 12], [3, 12],[5, 11], [6, 10]]
        self.tail_turrets = [[26, 12]]
        self.bottom_turrets = []

        # Current Support Locations
        self.prime_supports = []
        self.other_supports = []

        # base, up_base represent the current state of the structures
        self.turret_base = self.prime_turrets + self.tail_turrets + self.bottom_turrets
        self.wall_base = self.bandit_walls + self.top_right_walls + self.right_walls + self.bottom_walls + self.left_walls
        self.support_base = self.prime_supports + self.other_supports

        self.turret_up_base = [[3,12]]
        self.support_up_base = []
        self.wall_up_base = [[3,13], [2,13], [1, 13], [0,13]]

        self.upgrade_first =[[2, 12],[26, 12], [3, 12],[5, 11], [6, 10],[25,13],[24,13],[25,12]]


        # Lists (turrets and supports at calculated locations)
        # turrets and walls both are at turret_bq queue
        self.prime_turret_bq = [[[3,10],TURRET], [[1,12], TURRET],\
                                [[4,9],TURRET], [[7,9],TURRET],\
                                [[3,11], TURRET],[[5,8],TURRET],[[6,7],TURRET]]
        self.tail_turrets_bq = [[[25,12], TURRET],[[25,13], TURRET],\
                                [[24,12],TURRET], [[24,13],TURRET],[[23,12],WALL], [[23,13],TURRET],\
                                [[24,11],TURRET],\
                                [[23,11], TURRET],[[22,11], WALL],\
                                [[23,10], TURRET], [[22,10],WALL],\
                                ]
        

        self.support_bq = [[2, 11],[8,8],[8,5],[9,4],[9,5],\
                            [10,4],[11,4],[11,3],[11,2],[13,3]]

        self.turret_uq = [[[26, 13],WALL], [[26, 12], TURRET],\
                          [[2, 12], TURRET], [[6,11],WALL] , [[5, 11], TURRET],\
                          [[27,13], WALL], [[25,11], WALL],\
                          [[7,10], WALL], [[6,10], TURRET],[[8,9], WALL]\
                        ]
        self.support_uq = []

        # Strategy flags
        self.save_sp = 0
        self.epsilon_cut = 0.60
        self.no_response_cnt = 0
        self.after_demolisher=False

        self.exp_bandit = 0
        self.right_is_strong = False
        self.rich_th = 32

        # Utility instances
        self.enemy = Maze()

        self.free_path_req = [[0,13],[1,13],[1,12],[2,12],[2,11],[3,11],[23,9]]

        self.turret_base_tmp = []
        self.wall_base_tmp = []
        self.turret_up_base_tmp = []
        self.wall_up_base_tmp = []

        self.replace_units = []
        self.replacementFlag = False
        self.replace_th = 0.2
        self.iiti1_magic_numbers = [25,29,33,37,41,44,47,50,53,56,59]
        self.nextScoutFlag_iiti1 = False



    """Attacking Strategy!!  """
    def interceptor_location(self, game_state):
        # Calculating steps of enemy
        locations = [[13, 0], [14, 0]]
        result = []
        for loc in locations:
            path  = game_state.find_path_to_edge(loc)
            if(not isinstance(path, Iterable)):
                result.append(12)
            else:
                result.append((len(path) - 25)//2)
        if(result[0]<result[1]):
            if(result[0]>=14):
                return [14,0]
            else:
                return [7,6]
        else:
            return [7,6]

    def setAttack(self, game_state):
        cur_mp = game_state.get_resource(1)
        # Check Scout attack possibility

        # check for heavy attack
        int_sec = False
        if(game_state.turn_number in self.iiti1_magic_numbers):
            int_sec = True 

        if(int_sec == False):
            structureWeakFlag = True
            if(game_state.get_resource(1,1) >= 6):
                structureWeakFlag = False
            scoutToLeft = self.vishalakshi(game_state)        

            if(scoutToLeft==-1):
                self.no_response_cnt = 0
            else:
                self.no_response_cnt+=1

            if(scoutToLeft!=-1 and (structureWeakFlag == True or self.no_response_cnt >=2 or self.after_demolisher==True)):
                at_loc = [[13+scoutToLeft,0]]
                game_state.attempt_spawn(SCOUT, at_loc, 90)
        
        self.after_demolisher = False
        


        t = (3+ game_state.turn_number//10)

        # Is a bandit attack possible?



        # is Strong Attack?
       
        if(int_sec == False and t*game_state.type_cost(DEMOLISHER)[1]<=cur_mp):
            at_loc = [[14, 0]]
            if(self.enemy.weakSide(game_state) == False):
                at_loc = [[7, 6]]
                game_state.attempt_spawn(WALL, self.loc_walls)
                game_state.attempt_remove(self.loc_walls)
            game_state.attempt_spawn(DEMOLISHER, at_loc, t)
            self.after_demolisher=True

        # get mobile do boring stuff
        if(int_sec == True):
            nos = 3
            game_state.attempt_spawn(INTERCEPTOR, [[7,6]], 3)
        else:
            use_mp = self.getMobile(game_state)
            game_state.attempt_spawn(INTERCEPTOR, self.interceptor_location(game_state), use_mp)
        # Where to spawn?
        return

    def expensive_bandit(self, game_state, predicted_mp):
        hs, ut, nt, td = self.enemy.cornerStrength(game_state)
        ns_front = math.ceil(6*(hs) + 2*ut + 1*nt - 0.8*td) 
        ns_back = predicted_mp - ns_front

        if(ns_back<5):
            self.exp_bandit = False
            return -1
        return ns_front 
    

    def vishalakshi(self, game_state, max_scout=15):
        # Fetches points - Fast moving healthy units
        attack_report = self.path_danger_report(game_state)

        # locations = [[14,0], [13, 0]]
        # return 1 if right is better than left
        # return 2 if left is better than right

        right = 2
        damage_mn = 99999999
        for i in range(len(attack_report)):
            right-=1
            if(damage_mn > attack_report[i]):
                damage_mn = attack_report[i]
            if damage_mn <20:
                # self.touch_it_scout(game_state,toLeft=right, max_nos=max_scout)
                return right
        return -1


    def path_danger_report(self, game_state):
        location_options = [[14,0], [13,0]]
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if(not isinstance(path, Iterable)):
                damage = 250
            else:
                for path_location in path:
                    # Get number of enemy turrets that can attack each location and multiply by turret damage
                    damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return damages

    def calnext(self, round, st, use):
        return (st-use)*0.75 + round 

    def getMobile(self, game_state):
       
        t = 3*(3 + game_state.turn_number//10)
        cur_mp = game_state.get_resource(1)
        # Golden number for the demolisher deployement
        enemy_mp = game_state.get_resource(1,1)
        diff = enemy_mp-t
        rand_luck = random.random()


        disp_mp = cur_mp + (8/9)*(3-t) 
        if(disp_mp >= 1):
            return math.floor(disp_mp)

        r = 2+t/3
        disp_mp = 16*(7*r/4+9*cur_mp/16-t-1.5)/9
        if(disp_mp>=1):
            return math.floor(disp_mp)
        
        k = min(math.ceil(t/6), 3)
        if(diff<0):
            if(rand_luck<=0.8):
                return k-1
            else:
                return k
            
        else:
            if(rand_luck<=0.8):
                return k
            else:
                return k-1

    """---------------------------Break point----------------------------------"""
    def analyzeSelf(self, game_state):
        # SCANNIG SELF AREA FOR DEFENSE
        # SCAN ENEMY AREA FOR ATTACK
        # comparing with current base
        base_units = self.turret_base + self.wall_base
        com = [0,0]
        tot_damage = 0
        for loc in base_units:
            unit = game_state.contains_stationary_unit(loc)
            if unit==False:
                com[0] += loc[0]
                com[1] += loc[1]
                tot_damage+=1
            else:
                damage = (unit.max_health-unit.health)/unit.max_health
                com[0] += loc[0]*damage
                com[1] += loc[1]*damage
                tot_damage+=damage
        if(tot_damage<1):
            return 0
        com[0]/=tot_damage
        com[1]/=tot_damage

        # focus_side = self.closePoint(com)
        if(com[0]<=13):
            return 0
        else:
            return 1
    def chooseSide(self, game_state):
        t = game_state.turn_number//10
        d = [0.5 + 0.05*t, 1]
        r = random.random()
        cnt = -1
        for i in d:
            cnt+=1
            if r<=i:
                return cnt
        return 0

    def setDefense(self, game_state):
       
        
        if(self.replacementFlag == True):
            for loc, unit in self.replace_units:
                game_state.attempt_spawn(unit, loc)
                game_state.attempt_upgrade(loc)
            self.replace_units = []
            self.replacementFlag = False 

        # Check for the health of the crucial pieces and plan for rearranngement
        #  self.previous_round_build_order 
        # fs = self.analyzeSelf(game_state)
        fs = self.chooseSide(game_state)
        # Ensure the base defense is present
        self.buildBase(game_state)
        # Focus on the focus_side
        epsilon = random.random()
        # gamelib.debug_write("fs:",fs, "round: ", game_state.turn_number)
        
        # epsilon = 0.75

        if(epsilon<self.epsilon_cut):
            self.turret_uq = self.buildExploit(game_state, self.turret_uq)

            if(fs==1):
                self.tail_turrets_bq = self.buildExplore(game_state, self.tail_turrets_bq)
                self.prime_turret_bq = self.buildExplore(game_state, self.prime_turret_bq)
                self.buildSupport(game_state, game_state.get_resource(0))

               
            else:
                self.prime_turret_bq = self.buildExplore(game_state, self.prime_turret_bq)
                self.tail_turrets_bq = self.buildExplore(game_state, self.tail_turrets_bq)
                self.buildSupport(game_state, game_state.get_resource(0))
              
        else:
            self.buildSupport(game_state, game_state.get_resource(0))
            self.prime_turret_bq = self.buildExplore(game_state, self.prime_turret_bq)
            self.tail_turrets_bq = self.buildExplore(game_state, self.tail_turrets_bq)
        
        # gamelib.debug_write(disp_sp)
        
        
        replace_locations = []
        for loc in [[0,13],[27,13],[1,13],[26,13],[1,12],[26,12],[2,12],[25,12],[5,11]]:
            unit = game_state.contains_stationary_unit(loc)
            if(unit == False):
                continue 
            if(unit.health/unit.max_health <= self.replace_th):
                replace_locations.append(loc)

        self.replaceDefense(game_state,replace_locations)
        return 
        
        # base locations contain the expected progress so far
        # set difference would give the backlog/ damaged area


        # Base defense is build enough so change the current structure for the strategy
        # Defense implementation

        # After doing every thing check if something's needed to be replaced
        # self.check_weak_buildings at the borders


    def buildBase(self, game_state, supportFlag = 1):
        

        game_state.attempt_spawn(WALL,self.wall_base)

        for loc in self.turret_base :
             game_state.attempt_spawn(TURRET,loc)
             if(loc in self.upgrade_first and loc in self.turret_up_base and game_state.turn_number>20) :
                 game_state.attempt_upgrade(loc)

        if(len(self.wall_up_base)>0):
            game_state.attempt_upgrade(self.wall_up_base)
        if(len(self.turret_up_base)>0):
            game_state.attempt_upgrade(self.turret_up_base)

        if(supportFlag==1):
            if(len(self.support_base)>0):
                game_state.attempt_spawn(SUPPORT, self.support_base)
            if(len(self.support_up_base)):
                game_state.attempt_upgrade(self.support_up_base)
            # It has made sure to build or upgrade the base promised structure of that time
        return
    
    
    def dist(self, loc1, loc2):
        # using manhattan distance for the distance
        return abs(loc1[0]-loc2[0]) + abs(loc1[1]-loc2[1])

    def buildExplore(self, game_state, unit_list):
        disp_sp = game_state.get_resource(0)-self.save_sp 
        
        while(disp_sp>0 and len(unit_list)>0):
            gamelib.debug_write("eplore loop: " )

            loc, unit = unit_list[0]
            if(game_state.can_spawn(unit, loc)):
                game_state.attempt_spawn(unit, loc)
                disp_sp= disp_sp - game_state.type_cost(unit)[0]
                unit_list.pop(0)
                self.turret_uq.append([loc, unit])
                if(unit==TURRET):
                    self.turret_base.append(loc)
                    if(random.random()<0.6 and disp_sp>=4):
                        game_state.attempt_upgrade(loc)
                        disp_sp-=4
                elif(unit==WALL):
                    self.wall_base.append(loc)
            elif(disp_sp<game_state.type_cost(unit)[0]):
                break
            else:
                unit_list.pop(0)
        return unit_list
    
    def buildExploit(self, game_state, unit_list):
        gamelib.debug_write("exploit", unit_list)
        disp_sp = game_state.get_resource(0)-self.save_sp

        wall_cost = 1
        turret_cost = 4

        while(disp_sp>=wall_cost and len(unit_list)>0):
            gamelib.debug_write("Exploit loop: ")

            loc, unit = unit_list[0]
            cur_unit = game_state.contains_stationary_unit(loc)
            if(cur_unit==False):
                unit_list.pop(0)
                continue
            if(unit==TURRET and disp_sp>=turret_cost):
                game_state.attempt_upgrade(loc)
                disp_sp-=turret_cost
                self.turret_up_base.append(loc)
                unit_list.pop(0)
            elif(unit==WALL and disp_sp>=wall_cost):
                game_state.attempt_upgrade(loc)
                disp_sp-=wall_cost 
                self.wall_up_base.append(loc)
                unit_list.pop(0)
            else:
                break
        return unit_list

            
    def buildSupport(self, game_state, bal):
        disp_sp = bal
        support_cost = 4
        gamelib.debug_write("BuildSupport: ", bal )
        if(disp_sp<support_cost):
            return              

        while(disp_sp>=support_cost and len(self.support_uq)>0):
            loc = self.support_uq[0]
            unit = game_state.contains_stationary_unit(loc)

            if(unit == False):
                self.support_uq.pop(0)
                self.support_bq.append(loc)
                continue
            if(unit.upgraded == True):
                self.support_uq.pop(0)
            else:
                game_state.attempt_upgrade(loc)
                self.support_uq.pop(0)
                disp_sp -= support_cost
        
        while(disp_sp>=support_cost and len(self.support_bq)>0):
            loc = self.support_bq[0]
            unit = game_state.contains_stationary_unit(loc)

            if(unit == False):
                game_state.attempt_spawn(SUPPORT, loc)
                self.support_bq.pop(0)
                self.support_uq.append(loc)
                disp_sp-=support_cost
                self.buildSupport(game_state, disp_sp)
            else:
                self.support_bq.pop(0)
        return
    def replaceDefense(self, game_state, locations):
        replaced = []
        disp_sp = game_state.get_resource(0) - self.save_sp
        turret_cost = 6
        wall_cost = 2
        for loc in locations:
            unit = game_state.contains_stationary_unit(loc)
            if(unit == False):
                continue
            if(unit.unit_type == TURRET and disp_sp>=turret_cost):
                disp_sp -= turret_cost
                replaced.append([loc, TURRET])
                game_state.attempt_remove(loc)
            elif(unit.unit_type == WALL and disp_sp >= wall_cost):
                disp_sp-=wall_cost
                replaced.append([loc, WALL])
                game_state.attempt_remove(loc)
            elif(disp_sp<wall_cost):
                break 
        self.replace_units = replaced
        self.replacementFlag = True 
        return replaced






    def closePoint(self, location):
        left_loc = [0,13]
        right_loc = [27,13]
        bottom_loc = [13,0]

        # left = 0
        # right = 1
        # bottom = 2

        distances = [self.dist(left_loc, location),self.dist(right_loc, location),self.dist(bottom_loc, location)]
        # sum = 0
        # prev = 0
        # for i in distances:
        #     sum+=i
        # rnd_i = random.random()
        # for i in range(3):
        #     distances[i] = prev + distances[i]/sum
        #     prev = distances[i]
        #     if(distances[i]>=rnd_i):
        #         return i
        ind = 0
        mx = 100000
        for i in range(3):
            if(distances[i]<mx):
                mx = distances[i]
                ind = i
        return ind
    
    def setIIT1Attack(self, game_state):
        self.setAttack(game_state)
        if(self.nextScoutFlag_iiti1 == True):
            game_state.attempt_spawn(SCOUT, [14,0], 20)
            self.nextScoutFlag_iiti1 = False
        turn = game_state.turn_number
        if(turn in self.iiti1_magic_numbers):
            game_state.attempt_spawn(INTERCEPTOR, [[7,6]], 3)
        t = turn//10 + 5 
        if(game_state.get_resource(1)>=t*gamelib.GameUnit(DEMOLISHER).cost):
            game_state.attempt_spawn(DEMOLISHER, [[7,6]], t)
            self.nextScoutFlag_iiti1 = True
        



""""----------------------------------------------------------------------"""
class Detector():
    def __init__(self):
        self.yes = False 
        self.state = 0
        self.fix = False
        self.htl = [[8, 16], [20,16]]
        self.hsl = [[13,25], [14,25]]
        self.nos = True 

    def detect_iiti1(self, game_state):
        if(self.fix == True):
            return self.yes 
        else:
            tl = []
            sl = []
            for y in range(14, 28):
                for x in range(y-14,42-y):
                    unit = game_state.contains_stationary_unit([x,y])
                    if(unit == False):
                        continue
                    if(unit.unit_type == TURRET):
                        tl.append([x,y])
                    elif(unit.unit_type == SUPPORT):
                        sl.append([x,y])

            if(game_state.turn_number == 1):
                if(tl ==self.htl and sl == self.hsl):
                    self.state+=1
                    self.htl = [[3,15], [25,15], [8,16], [14,16], [20,16]]
                else:
                    self.fix = True
                    self.yes = False
                    return False
            elif(2<=game_state.turn_number<=5):
                if(tl == self.htl and sl==self.hsl):
                    self.state+=1
                else:
                    self.fix = True
                    self.yes = False
                    return False
            
            if(self.nos == True and game_state.get_resource(1,1) != 5):
                self.nos = False
            
            if(self.nos == True and self.state == 5):
                self.fix = True 
                self.yes == True 
                return True 
             

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        self.isIITI1 = False

        """"Upgrade the locations that are followed by double # comments!!"""



    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.bunker_inst = Bunker()
        self.iiti1_detector = Detector()

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.bunker_inst.setDefense(game_state)
        self.isIITI1 = self.iiti1_detector.detect_iiti1(game_state)
        if(self.isIITI1 == True):
            self.bunker_inst.setIIT1Attack(game_state)
        else:
            self.bunker_inst.setAttack(game_state)
        game_state.submit_turn()


    # Our strategy ends here

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # game_state.attempt_spawn(SCOUT, [24, 10], 1000)
        # return
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some supports
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
