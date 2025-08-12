import igraph
import os
import traceback
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import simpn.assets as assets
from simpn.visualisation import Shape, Hook, PlaceViz, Edge, Node
from time import time
from enum import Enum, auto
import math
import imageio
from typing import Literal


MAX_SIZE = 1920, 1080
# colors
TUE_RED = (200, 25, 25)
TUE_LIGHTRED = (249, 204, 204)
TUE_BLUE = (16, 16, 115)
TUE_LIGHTBLUE = (188, 188, 246)
TUE_GREY = (242, 242, 242)
WHITE = (255, 255, 255)
# sizes
STANDARD_NODE_WIDTH, STANDARD_NODE_HEIGHT = 50, 50
NODE_SPACING = 100
GRID_SPACING = 50
LINE_WIDTH = 2
ARROW_WIDTH, ARROW_HEIGHT = 12, 10
TEXT_SIZE = 16


class CustomPlaceViz(PlaceViz):
    def __init__(self, model_node):
        super().__init__(model_node)
        self._last_time = None
        self._curr_time = 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._half_height)
        pygame.draw.circle(screen, TUE_BLUE, (self._pos[0], self._pos[1]), self._half_height, LINE_WIDTH)    
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)
        bold_font = pygame.font.SysFont('Calibri', TEXT_SIZE, bold=True)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))

        # draw marking
        markings = [ token for token in self._model_node.marking ]
        last_time = self._last_time
        radius = self._half_height * 0.5  # distance from center for small circles
        small_radius = self._half_height * 0.18
        n = 8
        if (len(markings) < n):
            for i,token in enumerate(markings):
                angle = 2 * math.pi * i / n  # angle in radians
                x_offset = radius * math.cos(angle)
                y_offset = radius * math.sin(angle)
                color = TUE_GREY if token.time <= self._curr_time else TUE_RED
                pygame.draw.circle(
                    screen, color,
                    (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                    int(small_radius)
                )
                pygame.draw.circle(
                    screen, pygame.colordict.THECOLORS.get('black'),
                    (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                    int(small_radius),
                    LINE_WIDTH
                )
                if last_time is None:
                    last_time = round(token.time, 2)
                elif last_time < token.time:
                    last_time = round(token.time, 2)
            mstr = f"last @ {last_time}"
        else:

            count = len(markings)
            for i,token in enumerate(markings):
                if (i < n):
                    angle = 2 * math.pi * i / n  # angle in radians
                    x_offset = radius * math.cos(angle)
                    y_offset = radius * math.sin(angle)
                    color = TUE_GREY if token.time <= self._curr_time else TUE_RED
                    pygame.draw.circle(
                        screen, color,
                        (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                        int(small_radius)
                    )
                    pygame.draw.circle(
                        screen, pygame.colordict.THECOLORS.get('black'),
                        (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                        int(small_radius),
                        LINE_WIDTH
                    )
                if last_time is None:
                    last_time = round(token.time, 2)
                elif last_time < token.time:
                    last_time = round(token.time, 2)

            label = bold_font.render(f"{n}+", True, TUE_RED)
            screen.blit(label, (self._pos[0]-self._half_height * 0.25, self._pos[1]-self._half_height * 0.25))
            mstr = f"(x{count}) last @ {last_time}"
            
        label = bold_font.render(mstr, True, TUE_RED)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH + int(label.get_height())
        screen.blit(label, (text_x_pos, text_y_pos))      
        if (last_time != None): 
            self._last_time = last_time 
    

class Visualisation:
    """
    A class for visualizing the provided simulation problem as a Petri net.

    Attributes:
    - sim_problem (SimProblem): the simulation problem to visualize
    - layout_file (str): the file path to the layout file (optional)
    - grid_spacing (int): the spacing between grid lines (default: 50)
    - node_spacing (int): the spacing between nodes (default: 100)
    - layout_algorithm (str): the layout algorithm to use (default: "auto"), possible values: auto, sugiyama, davidson_harel, grid

    Methods:
    - save_layout(self, filename): saves the layout to a file
    - show(self): shows the visualisation
    """
    def __init__(self, 
        sim_problem, 
        layout_file=None, 
        grid_spacing=50, 
        node_spacing=100, 
        layout_algorithm:Literal["auto", "sugiyama","davidson_harel","grid"]='auto',
        record=False
        ):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Petri Net Visualisation')
        assets.create_assets(assets.images, "assets")
        icon = pygame.image.load('./assets/logo.png')
        pygame.display.set_icon(icon)

        self._grid_spacing = grid_spacing
        self._node_spacing = node_spacing
        self._layout_algorithm = layout_algorithm

        self.__running = False
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        self._selected_nodes = None        
        self._zoom_level = 1.0
        self._size = MAX_SIZE
        self._frames = []
        self._record = record
        self._speed = 1
        self._speed_complete = 0
        self._speed_time = 0

        # Add visualizations for prototypes, places, and transitions,
        # but not for places and transitions that are part of prototypes.
        element_to_prototype = dict()  # mapping of prototype element ids to prototype ids
        viznodes_with_edges = []
        for prototype in self._problem.prototypes:
            if prototype.visualize:
                prototype_viznode = prototype.get_visualisation()
                self._nodes[prototype.get_id()] = prototype_viznode
                if prototype.visualize_edges:
                    viznodes_with_edges.append(prototype_viznode)
                for event in prototype.events:
                    element_to_prototype[event.get_id()] = prototype.get_id()
                for place in prototype.places:
                    element_to_prototype[place.get_id()] = prototype.get_id()
        for var in self._problem.places:
            if var.visualize and var.get_id() not in element_to_prototype:
                self._nodes[var.get_id()] = CustomPlaceViz(var)
        for event in self._problem.events:
            if event.visualize and event.get_id() not in element_to_prototype:
                event_viznode = event.get_visualisation()
                self._nodes[event.get_id()] = event_viznode
                if event.visualize_edges:
                    viznodes_with_edges.append(event_viznode)
        # Add visualization for edges.
        # If an edge is from or to a prototype element, it must be from or to the prototype itself.
        for viznode in viznodes_with_edges:
            from_nodes = viznode._model_node.incoming
            to_nodes = viznode._model_node.outgoing
            if viznode._model_node.visualization_of_edges is not None:
                from_nodes = []
                to_nodes = []
                for (a, b) in viznode._model_node.visualization_of_edges:
                    if a == viznode._model_node:
                        to_nodes.append(b)
                    else:
                        from_nodes.append(a)
            for incoming in from_nodes:
                if incoming.visualize_edges:
                    node_id = incoming.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[:-len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(Edge(start=(other_viznode, Hook.RIGHT), end=(viznode, Hook.LEFT)))
            for outgoing in to_nodes:
                if outgoing.visualize_edges:
                    node_id = outgoing.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[:-len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(Edge(start=(viznode, Hook.RIGHT), end=(other_viznode, Hook.LEFT)))
        layout_loaded = False
        if layout_file is not None:
            try:
                self.__load_layout(layout_file)
                layout_loaded = True
            except FileNotFoundError as e:
                print("WARNING: could not load the layout because of the exception below.\nauto-layout will be used.\n", e)
        if not layout_loaded:
            self.__layout()        

        self.__win = pygame.display.set_mode(self._size, pygame.RESIZABLE) # the window

    
    def __draw(self):
        self.__screen = pygame.Surface(
            (self._size[0]/self._zoom_level, 
             self._size[1]/self._zoom_level)
        )
        self.__win.fill(TUE_GREY)
        self.__screen.fill(TUE_GREY)
        for shape in self._edges:
            shape._curr_time = self._problem.clock
            shape.draw(self.__screen)
        for shape in self._nodes.values():
            shape._curr_time = self._problem.clock
            shape.draw(self.__screen)
        self.__debug_info()
        # scale the entire screen using the self._zoom_level and draw it in the window
        self.__screen.get_width()
        self.__win.blit(pygame.transform.smoothscale(self.__screen, (self._size[0], self._size[1])), (0, 0))
        pygame.display.flip()

    def __debug_info(self):
        y = (5 / self._zoom_level)
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)
        # add the current time of the problem in the top left
        label = font.render(f"Current Clock: {round(self._problem.clock,2)}", True, TUE_RED)
        text_x_pos = 5 / self._zoom_level
        text_y_pos = (label.get_height() / self._zoom_level) + y
        self.__screen.blit(label, (text_x_pos, text_y_pos))
        y += (label.get_height() / self._zoom_level)

        text_x_pos = 5 / self._zoom_level
        text_y_pos = (label.get_height() / self._zoom_level) + y
        label = font.render(f"Speed: x{self._speed} ({self._speed_complete}) ({self._speed_time}ms)", True, TUE_RED)
        self.__screen.blit(label, (text_x_pos, text_y_pos))
        y += (label.get_height() / self._zoom_level)

        if (hasattr(self, "_slow_move_dur")):
            label = font.render(
                f"Rolling Duration Time: {round(self._slow_move_dur,1)} secs", 
                True, TUE_RED
            )
            text_x_pos = 5 / self._zoom_level
            text_y_pos = (label.get_height() / self._zoom_level) + y
            self.__screen.blit(label, (text_x_pos, text_y_pos))
            y+= (label.get_height() / self._zoom_level)

            if (self._problem.clock > 0):
                label = font.render(
                    f"Seconds to Clock: {round(self._slow_move_dur/self._problem.clock,1)} sec/cl",
                    True, TUE_RED
                    )
                text_x_pos = 5 / self._zoom_level
                text_y_pos = (label.get_height() / self._zoom_level) + y
                self.__screen.blit(label, (text_x_pos, text_y_pos))
                y+= (label.get_height() / self._zoom_level)

        

        

    def action_step(self):
        t = time()
        for s in range(self._speed):
            self._problem.step()
            if time() - t > 0.05:
                break
        self._speed_complete = s + 1
        self._speed_time = int((time() - t) * 1000)

    
    def __init_buttons(self):
        # No buttons for now.
        # btn_step = Button()        
        # pygame.draw.polygon(btn_step.image, TUE_RED, [(0, 0), (0, 30), (20, 15)])
        # pygame.draw.polygon(btn_step.image, TUE_RED, [(20, 0), (20, 30), (25, 30), (25, 0)])
        # btn_step.set_pos(self._size[0]-100, self._size[1]-50)
        # btn_step.action = self.action_step

        # return [btn_step]
        return []

    def __draw_buttons(self):
        for btn in self._buttons:
            btn.draw(self.__screen)

    def __click_button_at(self, pos):
        for btn in self._buttons:
            if btn.rect.collidepoint(pos):
                btn.action()
                return True
        return False

    def __layout(self):
        graph = igraph.Graph()
        graph.to_directed()
        for node in self._nodes.values():
            graph.add_vertex(node.get_id())
        for edge in self._edges:            
            graph.add_edge(edge.get_start_node().get_id(), edge.get_end_node().get_id())        
        if self._layout_algorithm == "auto":
            layout = graph.layout(layout="auto", )
        elif self._layout_algorithm == "sugiyama":
            layout = graph.layout_sugiyama()
        elif self._layout_algorithm == "davidson_harel":
            layout = graph.layout_davidson_harel()
        elif self._layout_algorithm == "grid":
            layout = graph.layout_grid()
        else:
            raise Exception(f"Unknown layout algorithm: {self._layout_algorithm}")
        layout.rotate(-90)
        layout.scale(self._node_spacing)
        boundaries = layout.boundaries(border=STANDARD_NODE_WIDTH*2)
        layout.translate(-boundaries[0][0], -boundaries[0][1])
        canvas_size = layout.boundaries(border=STANDARD_NODE_WIDTH*2)[1]
        self._size = (min(MAX_SIZE[0], canvas_size[0]), min(MAX_SIZE[1], canvas_size[1]))
        i = 0
        for v in graph.vs:
            xy = layout[i]
            xy  = (round(xy[0]/self._grid_spacing)*self._grid_spacing, round(xy[1]/self._grid_spacing)*self._grid_spacing)
            self._nodes[v["name"]].set_pos(xy)
            i += 1

    def zoom(self, action):
        """
        Zooms the model. Action can be one of: increase, decrease, reset.

        :param action: The zoom action to perform.
        """
        if action == "reset":
            self._zoom_level = 1.0
        elif action == "decrease":
            self._zoom_level /= 1.1
        elif action == "increase":
            self._zoom_level *= 1.1
        self._zoom_level = max(0.3, min(self._zoom_level, 3.0))  # clamp zoom level

    def fit_to_screen(self, padding=40):
        """
        Adjusts the zoom level so that all nodes fit within the window, with a given padding.
        :param padding: The minimum number of pixels to keep between nodes and the window edge.
        """
        if not self._nodes:
            return
        # Get bounding box of all nodes
        min_x = min(node.get_pos()[0] - getattr(node, '_width', STANDARD_NODE_WIDTH) / 2 for node in self._nodes.values())
        max_x = max(node.get_pos()[0] + getattr(node, '_width', STANDARD_NODE_WIDTH) / 2 for node in self._nodes.values())
        min_y = min(node.get_pos()[1] - getattr(node, '_height', STANDARD_NODE_HEIGHT) / 2 for node in self._nodes.values())
        max_y = max(node.get_pos()[1] + getattr(node, '_height', STANDARD_NODE_HEIGHT) / 2 for node in self._nodes.values())

        content_width = max_x - min_x + 50
        content_height = max_y - min_y + 50

        # Compute available width/height (minus padding on both sides)
        avail_width = self._size[0] - 2 * padding
        avail_height = self._size[1] - 2 * padding
        if content_width == 0 or content_height == 0:
            return
        # Compute zoom level
        zoom_x = avail_width / content_width
        zoom_y = avail_height / content_height
        zoom = min(zoom_x, zoom_y)
        # Clamp zoom level
        zoom = max(0.3, min(zoom, 3.0))
        self._zoom_level = zoom
        # Optionally, center the content (not required, but nice)
        offset_x = (self._size[0] / zoom - content_width) / 2 - min_x
        offset_y = (self._size[1] / zoom - content_height) / 2 - min_y
        for node in self._nodes.values():
            x, y = node.get_pos()
            node.set_pos((x + offset_x, y + offset_y))


    def save_layout(self, filename):
        """
        Saves the current layout of the nodes to a file.
        This method can be called after the show method.

        :param filename (str): The name of the file to save the layout to.
        """
        with open(filename, "w") as f:
            f.write("version 2.0\n")
            f.write(f"{self._zoom_level}\n")
            f.write(f"{int(self._size[0])},{int(self._size[1])}\n")
            for node in self._nodes.values():
                if "," in node.get_id() or "\n" in node.get_id():
                    raise Exception("Node " + node.get_id() + ": Saving the layout cannot work if the node id contains a comma or hard return.")
                f.write(f"{node.get_id()},{node.get_pos()[0]},{node.get_pos()[1]}\n")
    
    def __load_layout(self, filename):
        with open(filename, "r") as f:
            firstline = f.readline().strip()
            if firstline == "version 2.0":
                self._zoom_level = float(f.readline().strip())            
                self._size = tuple(map(int, f.readline().strip().split(",")))
            else:
                self._size = tuple(map(int, firstline.split(",")))
            for line in f:
                id, x, y = line.strip().split(",")
                if id in self._nodes:
                    self._nodes[id].set_pos((int(float(x)), int(float(y))))

    def __get_node_at(self, pos):
        scaled_pos = (pos[0] / self._zoom_level, pos[1] / self._zoom_level)
        for node in self._nodes.values():
            if node.get_pos()[0] - max(node._width/2, 10) <= scaled_pos[0] <= node.get_pos()[0] + max(node._width/2, 10) and \
            node.get_pos()[1] - max(node._height/2, 10) <= scaled_pos[1] <= node.get_pos()[1] + max(node._height/2, 10):
                return node
        return None


    def __drag(self, snap=False):
        nodes = self._selected_nodes[0]
        org_pos = self._selected_nodes[1]
        new_pos = pygame.mouse.get_pos()
        x_delta = new_pos[0] - org_pos[0]
        y_delta = new_pos[1] - org_pos[1]
        for node in nodes:
            new_x = node.get_pos()[0] + x_delta
            new_y = node.get_pos()[1] + y_delta
            if snap:
                new_x = round(new_x/GRID_SPACING)*GRID_SPACING
                new_y = round(new_y/GRID_SPACING)*GRID_SPACING
            node.set_pos((new_x, new_y))
        self._selected_nodes = nodes, new_pos

    def __start_slow_roll(self):
        self._slow_rolling = True 
        self._slow_move_done = False
        self._slow_move_start = time()
        self._slow_move_dur = 0
        self._slow_last = pygame.time.get_ticks()

    def __slow_roll(self):
        if not self._slow_move_done:
            self.action_step()
            self._slow_move_done = True
        if pygame.time.get_ticks() - self._slow_last >= 3 * (1000//30):
            self._slow_move_done = False 
            self._slow_last = pygame.time.get_ticks()
        self._slow_move_dur = time() - self._slow_move_start

    def __stop_slow_roll(self):
        self._slow_rolling = False
        self._slow_move_dur = 0
        
    def __handle_event(self, event):
        if event.type == pygame.QUIT:
            self.__running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            node = self.__get_node_at(event.pos)
            if node is not None:
                self._selected_nodes = [node], event.pos
            else:
                self._selected_nodes = self._nodes.values(), event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._selected_nodes is not None:
            self.__drag(snap=True)
            self._selected_nodes = None
        elif event.type == pygame.MOUSEMOTION and self._selected_nodes is not None:
            self.__drag()
        elif event.type == pygame.VIDEORESIZE:
            self._size = event.size
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._problem.step()
            elif event.key == pygame.K_r:
                self.__start_slow_roll()
            elif event.key == pygame.K_s:
                self.__stop_slow_roll()
            elif event.key == pygame.K_w:
                self._speed += 1
            elif event.key == pygame.K_e:
                self._speed = max(1, self._speed - 1)
            elif event.key == pygame.K_q:
                pygame.event.post(pygame.event.Event(pygame.QUIT))    
            elif event.key == pygame.K_SPACE:
                self.action_step()
            elif event.key == pygame.K_f:
                self.fit_to_screen()
            elif event.key == pygame.K_0 and event.mod & pygame.KMOD_CTRL:
                self.zoom("reset")
            elif event.key == pygame.K_MINUS and event.mod & pygame.KMOD_CTRL:
                self.zoom("decrease")
            elif event.key == pygame.K_EQUALS and event.mod & pygame.KMOD_CTRL:
                self.zoom("increase")
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.zoom("increase")
            else:
                self.zoom("decrease") 

    def show(self):
            """
            Displays the Petri net visualisation in a window.
            The method will block further execution until the window is closed.

            The visualisation can be interacted with using the mouse and keyboard.
            The spacebar can be used to step through the Petri net problem.
            The mouse can be used to drag nodes around.
            """
            clock = pygame.time.Clock()
            self.clock = clock
            self.__running = True
            self._slow_rolling = False
            zoomed = False
            while self.__running:
                for event in pygame.event.get():
                    self.__handle_event(event)
                try:
                    self.__draw()
                    if not zoomed:
                        self.fit_to_screen()
                        zoomed = True
                    if self._slow_rolling:
                        self.__slow_roll()
                    if (self._record):
                        frame = pygame.surfarray.array3d(pygame.display.get_surface())
                        frame = frame.transpose([1, 0, 2])  # Convert to (height, width, channels)
                        self._frames.append(frame)
                except Exception:
                    print("Error while drawing the visualisation.")
                    print(traceback.format_exc())
                    self.__running = False
                clock.tick(30)

            pygame.quit()
            if (self._record):
                print("Visualisation:: Writing record...")
                
                import os 
                i = 0
                name = f"output-{i:03d}.gif"
                while os.path.exists(name):
                    name = f"output-{i:03d}.gif"
                    i += 1

                imageio.mimsave(name,
                    self._frames,
                    fps=30,
                    palettesize=256,   
                    subrectangles=True 
                )

                print("Visualisation:: Finished writing record...")
                
