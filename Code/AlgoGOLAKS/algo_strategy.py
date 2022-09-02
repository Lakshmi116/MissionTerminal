from distutils.spawn import spawn
import queue
from socket import getnameinfo
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

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        self.bunker_turrets = [[3, 12], [3, 11], [6, 9], [7, 8], [7, 9]]
        self.prime_walls = [[7, 10], [6, 10], [8, 9], [8, 10], [4, 13], [4, 12], [4, 11], [3, 13]]
        self.heavy_bunker_turrets = [[4, 9], [9, 10]]
        self.prime_support_locations =  [[1,12],[2,12]]
        self.suppport_locations= [[2,11],[7,4]]
        self.bottom_right_walls = [[x, x-14] for x in range(18,28)] # Bottom Right wall
        self.bottom_walls = [[x, 5] for x in range(11,18)]          # Bottom wall
        self.bunker_tail = [[x, 16-x] for x in range(7,11)]         # Bunker Tail
        self.top_left_walls = [[x,13] for x in range(0,3)]         # Top Left Corner

        # Strategy Timers used to control the resources for the strategies
        # These timers are used whenever waiting is required for the strategy
        self.st_dem = 100
        self.st_sudden_defense = 100
        self.st_int_dem = 100
        self.st_scout_bot = 100

        # Strategy flags to represent that the online strategies
        self.sf_dem = False
        self.sf_sudden_defense = False
        self.sf_int_dem = False
        self.sf_scout_bot = False 





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

        self.GOLAKS(game_state)

        game_state.submit_turn()


    """Our Strategy.com"""
    
    def GOLAKS(self, game_state):
        self.setDefenseControl(game_state)
        self.setAttackStrategy(game_state)
        return 
        
# Never self destruct
# Consistency > Surprise Attack (not always)

# Level 0 Abstraction

    """
    Deploying strategy
    ----------------------------
    clean path => touch_it_scout (from turn_number>=4 always)
    ----------------------------
    1. 0-5 rounds: Interceptors defend the arena
    2. 5-10 rounds: level 1 dem_int
    3. 10-30 rounds: level 2 dem_int
    4. 30-40 rounds: level 3 dem_int
    5. 40-60 rounds: level 4 dem_int
    6. 60+ rounds: level 5 dem_int
    """

    def setDefenseControl(self, game_state):
        # Defense checks and restoration
        # Defense upgradation
        # Go Hand in with attack module to know it's structure points requriements
        self.vajra_kawachadhara(game_state)
        self.aayurvathi(game_state)
        return
    
    def setAttackStrategy(self, game_state):
        # Deployement strategy using MP
        # Structure points required only for loc (sp:[6, 9])
        turn = game_state.turn_number


        attackToLeft = 0
        defenseToLeft = 0
        demolisherAtTop = 0

        # Touch it Scout implementation
        pathFree = 0
        scoutToLeft = 0
        scout_nos = 5
        if(pathFree!=0):
            self.touch_it_scout(game_state, toLeft=scoutToLeft, max_nos = scout_nos)

        if(turn<5):
            # interceptors
            int_location = [[5,8]]
            self.only_interceptor(game_state,location=int_location, max_nos = 5)
        elif(turn<10):
            # level 1 dem_int
            self.dem_int_implementor(game_state,level=1,attackToLeft=attackToLeft, demolisherAtTop=demolisherAtTop,defenseToLeft=defenseToLeft)
        elif(turn<30):
            self.dem_int_implementor(game_state, level=2, attackToLeft=attackToLeft, demolisherAtTop=demolisherAtTop, defenseToLeft=defenseToLeft)
        elif(turn<40):
            self.dem_int_implementor(game_state, level=3, attackToLeft=attackToLeft, demolisherAtTop=demolisherAtTop, defenseToLeft=defenseToLeft)
        elif(turn<60):
            self.dem_int_implementor(game_state, level=4, attackToLeft=attackToLeft, demolisherAtTop=demolisherAtTop, defenseToLeft=defenseToLeft)
        else:
            self.dem_int_implementor(game_state, level=5, attackToLeft=attackToLeft, demolisherAtTop=demolisherAtTop, defenseToLeft=defenseToLeft)
        return 
   

# Level 1 abstraction 
    def vajra_kawachadhara(self, game_state):
        # Basic defense build up
        # Used in first 5 rounds. Opening move
        # return 
        if(game_state.turn_number<3):
            self.interceptor_attack(game_state)
        elif(game_state.turn_number==3):
            self.build_defense(game_state)

    
    def kala_bhairava(self, game_state):
        # Maintainance of defense
        # Upgrades defense system in a timely fashion

        wl1 = [[4,13], [4,12]]
        wl2 =  [[7, 8], [8, 7], [9, 6], [24, 13]]
        tl1 = [[3, 12], [3, 11], [6, 9], [7, 8]]
        tl2 = [ [25,13]]
        sl = [[2,12], [8,7]]
        game_state.attempt_upgrade(tl1)
        game_state.attempt_upgrade(wl1)
        game_state.attempt_upgrade(tl2)
        game_state.attempt_upgrade(wl2)
        game_state.attempt_upgrade(sl)
        return 

    def aswadalam(self, game_state):
        # Controls the loc and deploys demolishers to weaken the defense
        weak_x = self.border_weakness_report(game_state)
        self.demolisher_loc(game_state, (weak_x>14))
        self.demolisher_interceptor(game_state)


        return 

    def vishalakshi(self, game_state):
        # Fetches points - Fast moving healthy units
        attack_report = self.path_danger_report(game_state)

        # locations = [[13,0], [14, 0]]
        right = -1 
        for path_report in attack_report:
            right+=1
            damage = 0
            for i in path_report:
                damage+=i 
            if damage < 20:
                self.touch_it_scout(game_state,toLeft=right)
                return
    
    def aayurvathi(self, game_state):
        # Deploys support units in a timely fashion
        if(game_state.turn_number==3):
            game_state.attempt_spawn(SUPPORT,self.prime_support_locations)
            game_state.attempt_spawn(SUPPORT,self.suppport_locations)
        return 


# Level 2 Utilities 

    ### Defense
    def interceptor_attack(self, game_state, random_state=0, nos=3):
        # Interceptor deployement strategy

        if(random_state==0):
            locations = [[9,4], [14, 0], [10,3], [14, 0], [10,3]]
            game_state.attempt_spawn(INTERCEPTOR, locations)
        else:
            locations = [[9,4], [6, 7], [14, 0], [13, 0]]
            spawn = []
            for i in range(nos):
                ri = random.randint(0,len(locations)-1)
                spawn.append(locations[ri])
            game_state.attempt_spawn(INTERCEPTOR, spawn)
        return 
    
    def antiFoxDefense(self, game_state):
        # Defense strategy to contuor enemy's fox strategy

        return 

    
   

    ### Attacking

    def dem_int_implementor(self, game_state, level = 6, attackToLeft=0,  demolisherAtTop=0, defenseToLeft=0,):
        max_dem = 2*level
        max_int = max(1,level-1)

        deploy_1 = [[5,8]]
        deploy_2 = [[13,0]]
        deploy_3 = [[14,0]]
        deploy_4 = [[10,3]]

        dem_location = deploy_4 
        int_location = deploy_1

        # almost never use scenario
        if(defenseToLeft!=0):
            int_location = deploy_3 

        if(demolisherAtTop!=0):
            dem_location = deploy_1
        elif(attackToLeft!=0):
            dem_location = deploy_3

        if(game_state.can_spawn(DEMOLISHER,dem_location,max_dem)):
            self.only_demolisher(game_state, dem_location, max_dem)
            self.only_interceptor(game_state, int_location, max_int)
        elif(game_state.can_spawn(DEMOLISHER, dem_location, max_dem-2)):
            self.only_demolisher(game_state, dem_location, max_dem-2)
            self.only_interceptor(game_state, int_location, max_int)        
        else:
            self.only_interceptor(game_state, int_location, max_int)
        return 


    def only_demolisher(self, game_state, location, max_nos=9):
        # Funtion to deploy only demolishers 
        nos = min(max_nos,math.floor(game_state.get_resources(1))//(gamelib.GameUnit(DEMOLISHER, game_state.config).cost))
        game_state.attempt_spawn(DEMOLISHER, location, nos)
        return 

    def only_interceptor(self, game_state, location, max_nos = 3):
        # Fucntion to deploy interceptors
        # By default interceptors are deployed at the bunker
        # So that by the time enemy units reach the bunker, interceptors could counter the attack

        nos = min(max_nos, math.floor(game_state.get_resources(1))//(gamelib.GameUnit(INTERCEPTOR, game_state.config).cost))
        game_state.attempt_spawn(INTERCEPTOR, location, nos)
        return 


    def touch_it_scout(self, game_state, toLeft=0):
        # Scout deployement strategy
        # Use this only from vishalakshi
        location = [[13, 0]]
        if toLeft!=0:
            location = [[14, 0]]
        nos = math.floor(game_state.get_resources(1))
        game_state.attempt_spawn(SCOUT, location,nos)
        return



    def demolisher_loc(self,game_state,size=0):
        # Controls loc to facilitate demolishers attacking frontline defense
        wl = [[x, 13] for x in range(5,10+3*size)]
        game_state.attempt_spawn(WALL,wl)

        # Making the recent wall temporary
        game_state.attempt_remove(wl)
        return 


    ### Sanity & Inspection
    
    def border_weakness_report(self, game_state):
        # easily attackble region at y = 15
        # returns the x location for the weakest zone

        weakest_x = 9
        weakness = 100
        for i in range(28):
            shields = len(game_state.get_attackers([i, 14], 0))
            if(shields<weakness):
                weakness = shields
                weakest_x = i
        return weakest_x 

        return 
    
    def path_danger_report(self, game_state):
        # Score the paths based on the predicted attack possible
        # scout score..

        start_x = [[13,0], [14,0]]
        paths = [game_state.find_path_to_edge(location) for location in start_x]

        # scout score = number of scouts required to make it until the end
        #  = total damage possible in the path/ scout tolerance
        #  scout tolerance depends on the shielding (basic + shielding points)
        attack_report = {}
        for path in paths:
            attack_report[path[0][0]] = [len(game_state.get_attackers(location, 0))*gamelib.GameUnit(TURRET, game_state.config).damage_i for location in path]
            
        return attack_report 


    
    def skeleton_fracture_report(self, game_state):
        # Regions that are damaged
        # Checks for Bottom Right, Bottom wall and Bunker Tail
        wh = gamelib.GameUnit(WALL, game_state.config).max_health
        
        brw = []
        for location in self.bottom_right_walls:
            brw.append(location.append(self.wall_health(game_state, location)/wh))
        bw = []
        for location in self.bottom_walls:
            bw.append(location.append(self.wall_health(game_state, location)/wh))
        tlw = []
        for location in self.top_left_walls:
            tlw.append(location.append(self.wall_health(game_state, location)/wh))
        btw = []
        for location in self.bunker_tail:
            btw.append(location.append(self.wall_health(game_state, location)/wh))
        return (brw, bw, tlw, btw)

    def dday_bunker_strength_report(self, game_state):
        # Head of the defense strength and attack capacity report
        # demolisher control score

        # returns the state of bunker turrets and prime walls
        th = gamelib.GameUnit(TURRET, game_state.config).max_health
        wh = gamelib.GameUnit(WALL, game_state.config).max_health
        bt = [self.turret_health(game_state, location)/th for location in self.bunker_turrets]
        pw = [self.wall_health(game_state, location)/wh for location in self.prime_walls]

        return (bt, pw)
    
    def isFoxAttack(self, game_state):
        # After Strategy Control

        return 

    ### Utility functions 
    def  build_defense(self,game_state):
        # wall skeleton
        wl = self.prime_walls
        wl += self.bottom_right_walls  # Bottom Right wall
        wl += self.bottom_walls   # Bottom wall
        wl += self.bunker_tail  # Bunker Tail
        wl += self.top_left_walls  # Top Left Corner

        # turret locations
        tl = self.bunker_turrets
        game_state.attempt_spawn(WALL,wl)
        game_state.attempt_spawn(TURRET,tl)
        return 

    def wall_health(self, game_state, location):
        item = game_state.game_map.__getitem__(location)
        if item[0].unit_type != game_state.config["unitInformation"][0]["shorthand"]:
            return 0
        return item.health
    
    def turret_health(self, game_state, location):
        item = game_state.game_map.__getitem__(location)
        if item[0].unit_type != game_state.config["unitInformation"][1]["shorthand"]:
            return 0
        return item.health
    
    def save_mobile(self, game_state, goal=0, spendAllowance=0, rounds=0):
        # Use this function to save Mobile points for any future operations

        return




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
