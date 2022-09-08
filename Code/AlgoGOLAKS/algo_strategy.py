from argparse import SUPPRESS
from dis import dis
# from distutils.spawn import spawn
from collections.abc import Iterable
import queue
from socket import getnameinfo
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

class Bunker():
    def __init__(self):
        # seed = random.randrange(maxsize)
        # random.seed(seed)
        # Current wall locations
        self.bandit_walls = [[0, 13], [1, 13],[2, 13], [3, 13]]
        self.top_right_walls = [[26, 13], [27, 13]]
        self.right_walls = [[25, 11], [24, 10], [23, 9], [22, 8], [21, 7], [20, 6]]
        self.bottom_walls = [[12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 5], [18, 6], [19, 6]]
        self.left_walls = [[6, 11], [7, 10], [8, 9], [9, 8], [10, 7], [11, 6]]

        # Current Turret Locations (!!Remove!!)
        self.prime_turrets = [[2, 12], [3, 12], [5, 11], [6, 10]]
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


        # Lists (turrets and supports at calculated locations)
        # turrets and walls both are at turret_bq queue
        self.prime_turret_bq = [[[3,10],TURRET], [[1,12], TURRET],\
                                [[4,9],TURRET], [[7,9],TURRET],\
                                [[3,11], TURRET]]
        self.tail_turrets_bq = [[[25,12], TURRET],[[25,13], WALL],\
                                [[24,12],TURRET], [[24,13],WALL],[[23,12],WALL], [[23,13],WALL],\
                                [[24,11],TURRET],\
                                [[23,11], TURRET],[[22,11], WALL],\
                                [[23,10], TURRET], [[22,10],WALL],\
                                ]
        self.bottom_turrets_bq = [[[10,6],TURRET], [[16,5], TURRET], [[13,5],TURRET]]

        self.support_bq = [[2, 11], [6, 7], [7, 7], [9, 7], [7, 6],\
                           [9, 6], [10, 6], [11, 5], [11, 2], [12, 2],\
                           [12, 1]]

        self.turret_uq = [[[26, 13],WALL], [[26, 12], TURRET],\
                          [[2, 12], TURRET], [[6,11],WALL] , [[5, 11], TURRET],\
                          [[27,13], WALL], [[25,11], WALL],\
                          [[7,10], WALL], [[6,10], TURRET],[[8,9], WALL]\
                        ]
        self.support_uq = []

        # Strategy flags
        self.save_sp = 0
        self.epsilon_cut = 0.75
        self.no_response_cnt = 0
    """Attacking Strategy!!  """
    def setAttack(self, game_state):
        cur_mp = game_state.get_resource(1)
        # Check Scout attack possibility

        structureWeakFlag = True
        if(game_state.get_resource(1)[0] >= 8):
            structureWeakFlag = False
        scoutToLeft = self.vishalakshi(game_state)        

        if(scoutToLeft==-1):
            self.no_response_cnt = 0
        else:
            self.no_response_cnt+=1

        if(scoutToLeft!=-1 and (structureWeakFlag == True or self.no_response_cnt >=2)):
            at_loc = [[13+scoutToLeft,0]]
            game_state.attempt_spawn(SCOUT, at_loc, 90)

        # is Strong Attack?
        t = (3+ game_state.turn_number//10)
        if(t*game_state.type_cost(DEMOLISHER)[1]<=cur_mp):
            at_loc = [[5, 8]]
            game_state.attempt_spawn(DEMOLISHER, at_loc, t)

        # get mobile do boring stuff
        use_mp = self.getMobile(game_state)
        game_state.attempt_spawn(INTERCEPTOR, [[5, 8]], use_mp)
        # Where to spawn?
        return 
        
    def vishalakshi(self, game_state, max_scout=15):
        # Fetches points - Fast moving healthy units
        attack_report = self.path_danger_report(game_state)

        # locations = [[13,0], [14, 0]]
        # return 1 if right is better than left
        # return 2 if left is better than right

        right = -1 
        isLeft = 0
        damage_mn = 99999999
        for damage in attack_report:
            right+=1
            if(damage_mn > damage):
                damage_mn = damage
                isLeft = right
            if damage <5:
                # self.touch_it_scout(game_state,toLeft=right, max_nos=max_scout)
                return right
        return -1

    def path_danger_report(self, game_state):
        location_options = [[13,0], [14,0]]
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
        disp_mp = cur_mp + (8/9)*(3-t) 
        if(disp_mp >= 1):
            return math.floor(disp_mp)
        disp_mp = 16*(4*(t/3) + 9*cur_mp/16+12.5)/9
        if(disp_mp>=1):
            return math.floor(disp_mp)
        return min(math.ceil(t/6), 3)

    """
    TODO
    ----
    1. Incrementally add turrets, supports and upgrades
    2. Attack strategty based on minimal waste and timely heavy damage
    3. Attack on the weak side
    4. Heavy attack at border strategy.....!!

    """
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
    def chooseSide(self):
        d = [0.7, 0.95, 1]
        r = random.random()
        cnt = -1
        for i in d:
            cnt+=1
            if r<=i:
                return cnt
        return 0

    def setDefense(self, game_state):
        # Check for the health of the crucial pieces and plan for rearranngement
        #  self.previous_round_build_order 
        # fs = self.analyzeSelf(game_state)
        fs = self.chooseSide()
        # Ensure the base defense is present
        self.buildBase(game_state)
        # Focus on the focus_side
        epsilon = random.random()
        # gamelib.debug_write("fs:",fs, "round: ", game_state.turn_number)
        
        # epsilon = 0.75

        if(epsilon<self.epsilon_cut):
            self.turret_uq = self.buildExploit(game_state, self.turret_uq)

            if(fs==2):
                self.bottom_turrets_bq = self.buildExplore(game_state, self.bottom_turrets_bq)
            elif(fs==1):
                self.tail_turrets_bq = self.buildExplore(game_state, self.tail_turrets_bq)
            else:
                self.prime_turret_bq = self.buildExplore(game_state, self.prime_turret_bq)
        else:
            # if(fs==2):
            #     self.bottom_turrets_bq = self.buildExplore(game_state, self.bottom_turrets_bq)
            # elif(fs==1):
            #     self.tail_turrets_bq = self.buildExplore(game_state, self.tail_turrets_bq)
            # else:
            #     self.prime_turret_bq = self.buildExplore(game_state, self.prime_turret_bq)
            self.buildSupport(game_state, game_state.get_resource(0))
        
        # gamelib.debug_write(disp_sp)
        return 
        
        # base locations contain the expected progress so far
        # set difference would give the backlog/ damaged area


        # Base defense is build enough so change the current structure for the strategy
        # Defense implementation

        # After doing every thing check if something's needed to be replaced
        # self.check_weak_buildings at the borders


    def buildBase(self, game_state, supportFlag = 1):
        
        game_state.attempt_spawn(WALL,self.wall_base)
        game_state.attempt_spawn(TURRET, self.turret_base)

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

""""----------------------------------------------------------------------"""
class Maze():
    def __init__(self):
        pass 

    def setDefense(self, gamae_state):
        pass 
    def setAttack(self, game_state):
        pass 

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

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
