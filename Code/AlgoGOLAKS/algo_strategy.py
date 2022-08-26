from distutils.spawn import spawn
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

        self.bottom_right_walls = [[x, x-14] for x in range(18,28)] # Bottom Right wall
        self.bottom_walls = [[x, 5] for x in range(11,18)]          # Bottom wall
        self.bunker_tail = [[x, 16-x] for x in range(7,10)]         # Bunker Tail
        self.top_left_walls = [[x,13] for x in range(0,3)]         # Top Left Corner


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
        if(game_state.turn_number<5):
            self.interceptor_attack(game_state, random_state=0)
        else:
            self.vajra_kawachadhara(game_state)
            self.interceptor_attack(game_state, random_state=1)
            self.kala_bhairava(game_state)
        
   
    
   

# Level 1 abstraction 
    def vajra_kawachadhara(self, game_state):
        # Basic defense build up
        # Used in first 5 rounds. Opening move
        # return 
        wall_locations,turret_locations= self.hc()
        game_state.attempt_spawn(WALL,wall_locations)
        game_state.attempt_spawn(TURRET,turret_locations)
    
    
    
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

        locations = [[13,0], [14, 0]]
        right = -1 
        for path_report in attack_report:
            right+=1
            damage = 0
            for i in path_report:
                damage+=i 
            if damage < 20:
                self.touch_it_scout(game_state,toleft=right)
                break 
        return
    
    def aayurvathi(self, game_state):
        # Deploys support units in a timely fashion
        support_locations =  [[2,12], [8,7]]
        game_state.attempt_spawn(SUPPORT,support_locations)

        return 

    def eedhi_maranam(self, game_state):
        # Interceptor strategy when defense is collapsed (no or low demolisher score)

        return 

# Level 2 Utilities 

    ### Defense

            
    def interceptor_guerrilla_warfare(self, game_state):
        # Deploys interceptors in random regions to eat up demolishers and scouts

        pos = random.randint(0,3)
        interceptor_pos = [[3+pos,13-pos]]
        game_state.attempt_spawn(INTERCEPTOR,interceptor_pos,5)
        return 


    def motion_less_blockage():
        # Blocks all the paths of opponent to save mobile points
        # Time complexity is a bit high for the value it adds to the strategy
        # Implement at the end if time permits

        return 
    



    ### Attacking

    def demolisher_loc(self,game_state,size=0):
        # Controls loc to facilitate demolishers attacking frontline defense
        wl = [[5,12]]
        wl += [[x, 13] for x in range(6,10+3*size)]
        game_state.attempt_spawn(WALL,wl)

        # Making the recent wall temporary
        game_state.attempt_remove(wl)
        return 



        

    def demolisher_interceptor(self,game_state,edge=0):
        # Continous deployment of demolisher interceptor pairs
        # Clear the already weak path for the slow moving interceptors
        demolisher_loc = [[3,10]]
        game_state.attempt_spawn(DEMOLISHER,demolisher_loc,1)
        interceptor_loc = []
        pos = random.randint(0,2)
        if(edge==0) :
            interceptor_loc = [[4+pos,9+pos]]
        else :
            interceptor_loc = [[14+pos,0+pos]]
        game_state.attempt_spawn(INTERCEPTOR,interceptor_loc,1)


    def touch_it_scout(self, game_state, toleft=0):
        # Scout deployement strategy
        # Use this only from vishalakshi
        location = [13, 0]
        if toleft!=0:
            location = [14, 0]
        nos = math.floor(game_state.MP)
        locations = location*nos 
        game_state.attempt_spawn(SCOUT, locations)
        return

    def interceptor_attack(self, game_state, random_state=0, nos=3):
        # Interseptor deployement strategy

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
            
        
       
    

    def bandit_attack():
        # Most unused

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

    ### Utility functions 
    def hc(self):
        # wall skeleton
        wl = self.prime_walls
        wl += self.bottom_right_walls  # Bottom Right wall
        wl += self.bottom_walls   # Bottom wall
        wl += self.bunker_tail  # Bunker Tail
        wl += self.top_left_walls  # Top Left Corner

        # turret locations
        tl = self.bunker_turrets
        return (wl, tl)

    def wall_health(self, game_state, location):
        item = game_state.game_map.__getitem__(location)
        if item.unit_type != game_state.config["unitInformation"][0]["shorthand"]:
            return -120
        return item.health
    
    def turret_health(self, game_state, location):
        item = game_state.game_map.__getitem__(location)
        if item.unit_type != game_state.config["unitInformation"][1]["shorthand"]:
            return -150
        return item.health




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
