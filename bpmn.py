from simpn.prototypes import BPMNTask
import visualisation as vis
import pygame
import math

from abc import abstractmethod

class CustomBPMNTask(BPMNTask):
    """
    Custom BPMN Task to change the renderer.
    """

    def __init__(self, 
                 model, incoming, outgoing, 
                 name, behavior, 
                 guard=None, 
                 outgoing_behavior=None):
        super().__init__(
            model, incoming, outgoing,
              name, behavior, 
              guard, 
              outgoing_behavior)
        
    class BPMNTaskViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._width = 100
            self._height = vis.STANDARD_NODE_HEIGHT
            self._half_width =  self._width / 2
            self._half_height = self._height / 2
            self._early = None 
            self._late = None

        def draw(self, screen):
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.rect(screen, vis.TUE_LIGHTBLUE, pygame.Rect(x_pos, y_pos, self._width, self._height), border_radius=int(0.075*self._width))
            pygame.draw.rect(screen, vis.TUE_BLUE, pygame.Rect(x_pos, y_pos, self._width, self._height),  vis.LINE_WIDTH, int(0.075*self._width))
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = int((self._width - label.get_width())/2) + x_pos
            text_y_pos = int((self._height - label.get_height())/2) + y_pos
            screen.blit(label, (text_x_pos, text_y_pos))

            # draw marking
            self.__marking(screen, font)

        def __marking(self, screen, font):
            early = None
            last = self._late
            work = len(self._model_node._busyvar.marking)
            for token in self._model_node._busyvar.marking:
                time = token.time
                if early is None:
                    early = round(time,1) 
                elif early > time:
                    early = round(time,1)
                
                if last is None:
                    last = round(time,1)
                elif last < time:
                    last = round(time,1) 
            
            mstr = f"x{work} E: {early if early is not None else 'X'} L: {last}"

            label = font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))     
            if early is not None:
                self._early = early
            if last is not None:
                self._late = last
        
    def get_visualisation(self):
        return self.BPMNTaskViz(self)


class HelperBPMNTask(CustomBPMNTask):
    """
    Helper class for BPMNTask to allow easy subclassing and automatic registration with the model.
    Subclass this and implement the behaviour (and optionally guard and outgoing_behaviour) as static/class methods (no self argument).
    Set model, incoming, outgoing, and name as static class variables in your subclass.
    Just defining the class is enough; no instantiation needed.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Fetch static/class variables
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            # Don't register the abstract base class
            if cls.__name__ == 'HelperBPMNTask':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNTask subclass.")
        # Fetch static/class methods
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNTask subclass.")
        guard = getattr(cls, 'guard', None)
        outgoing_behaviour = getattr(cls, 'outgoing_behaviour', None)
        # If not implemented, set to None
        if guard is not None and not callable(guard):
            guard = None
        if outgoing_behaviour is not None and not callable(outgoing_behaviour):
            outgoing_behaviour = None
        # Register the task with the model by instantiating the subclass
        cls(model, incoming, outgoing, name, behaviour, guard=guard, outgoing_behavior=outgoing_behaviour)

    @staticmethod
    @abstractmethod
    def behaviour(*args):
        pass


# Helper class for BPMNStartEvent
from simpn.prototypes import BPMNStartEvent

class HelperBPMNStart(BPMNStartEvent):
    """
    Helper class for BPMNStartEvent to allow easy subclassing and automatic registration with the model.
    Subclass this and implement the interarrival_time as a static/class method (no self argument).
    Set model, outgoing, and name as static class variables in your subclass.
    Just defining the class is enough; no instantiation needed.
    """
    model = None
    outgoing = None
    name = None
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNStart':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        interarrival_time = getattr(cls, 'interarrival_time', None)
        if interarrival_time is None or not callable(interarrival_time):
            raise NotImplementedError("You must implement a static/class method 'interarrival_time()' in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        cls(model, [], outgoing, name, interarrival_time)

    @staticmethod
    @abstractmethod
    def interarrival_time():
        pass

from simpn.prototypes import BPMNEndEvent

class HelperBPMNEnd(BPMNEndEvent):
    """
    Helper class for BPMNEndEvent to allow easy subclassing and automatic 
    registration with the model.
    Subclass this and implement the interarrival_time as a static/class 
    method (no self argument).
    Set model, outgoing, and name as static class variables in your 
    subclass.
    Just defining the class is enough; no instantiation needed.
    """
    model = None
    incoming = None
    name = None
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or name is None:
            if cls.__name__ == 'HelperBPMNEnd':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        cls(model, incoming, [], name)

    class BPMNEndEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._last_time = None
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH*2)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

            # draw marking
            markings = [ token for token in self._model_node._captures ]
            last_time = self._last_time
            radius = self._half_height * 0.5  # distance from center for small circles
            small_radius = self._half_height * 0.18
            n = 8
            if (len(markings) < n):
                for i,token in enumerate(markings):
                    angle = 2 * math.pi * i / n  # angle in radians
                    x_offset = radius * math.cos(angle)
                    y_offset = radius * math.sin(angle)
                    pygame.draw.circle(
                        screen, vis.TUE_GREY,
                        (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                        int(small_radius)
                    )
                    pygame.draw.circle(
                        screen, pygame.colordict.THECOLORS.get('black'),
                        (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                        int(small_radius),
                        vis.LINE_WIDTH
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
                        pygame.draw.circle(
                            screen, vis.TUE_GREY,
                            (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                            int(small_radius)
                        )
                        pygame.draw.circle(
                            screen, pygame.colordict.THECOLORS.get('black'),
                            (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                            int(small_radius),
                            vis.LINE_WIDTH
                        )
                    if last_time is None:
                        last_time = round(token.time, 2)
                    elif last_time < token.time:
                        last_time = round(token.time, 2)

                label = bold_font.render(f"{n}+", True, vis.TUE_RED)
                screen.blit(label, (self._pos[0]-self._half_height * 0.25, self._pos[1]-self._half_height * 0.25))
                mstr = f"(x{count}) last @ {last_time}"
                
            label = bold_font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))      
            if (last_time != None): 
                self._last_time = last_time 

    def get_visualisation(self):
        return self.BPMNEndEventViz(self)

from simpn.prototypes import BPMNIntermediateEvent

class HelperBPMNIntermediateEvent(BPMNIntermediateEvent):
    """
    Helper class for BPMNIntermediateEvent to allow easy subclassing and automatic registration with the model.
    Subclass this and implement the behavior as a static/class method (no self argument).
    Set model, incoming, outgoing, and name as static class variables in your subclass.
    Just defining the class is enough; no instantiation needed.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNIntermediateEvent':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNIntermediateEvent subclass.")
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNIntermediateEvent subclass.")
        # Register the intermediate event with the model by instantiating BPMNIntermediateEvent
        cls(model, incoming, outgoing, name, behaviour)

    @staticmethod
    @abstractmethod
    def behaviour(*args):
        pass

    class BPMNIntermediateEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._early = None
            self._late = None
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH)   
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2-3, vis.LINE_WIDTH)   
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

            # draw marking

        def __marking(self, screen, font):
            early = None
            last = self._late
            print(f"Marking for {self._model_node.get_id()}: {[attr for attr in self._model_node.__dict__ ]}")
            work = len(self._model_node._busyvar.marking)
            for token in self._model_node._busyvar.marking:
                time = token.time
                if early is None:
                    early = round(time,1) 
                elif early > time:
                    early = round(time,1)
                
                if last is None:
                    last = round(time,1)
                elif last < time:
                    last = round(time,1) 
            
            mstr = f"x{work} E: {early if early is not None else 'X'} L: {last}"

            label = font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))     
            if early is not None:
                self._early = early
            if last is not None:
                self._late = last

    def get_visualisation(self):
        return self.BPMNIntermediateEventViz(self)


from simpn.prototypes import BPMNExclusiveSplitGateway

class HelperBPMNExclusiveSplit(BPMNExclusiveSplitGateway):
    """
    Subclass this to define an exclusive split gateway in BPMN with minimal boilerplate.
    Set class variables: model, incoming, outgoing, name.
    Implement a `choice` method (no self argument).
    Registration is automatic on class definition.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    def __init_subclass__(cls):
        # Import here to avoid circular imports
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        if not hasattr(cls, "choice"):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define a 'choice' method.")
        # Register the gateway automatically
        cls(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            cls.choice
        )

    @staticmethod
    @abstractmethod
    def choice(c):
        pass