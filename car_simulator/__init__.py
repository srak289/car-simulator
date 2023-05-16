class CarBase(object): pass
class TransmissionBase(object): pass
class EngineBase(object): pass

class Engine(EngineBase):
    class EngineError(Exception): pass
    class EngineOffError(EngineError): pass
    class EngineRedlineError(EngineError): pass
    class EngineDestroyedError(EngineError): pass
    class NoTransmissionError(EngineError): pass

    def __init__(self, car: CarBase, rpm_max, rpm_idle, sport=False):
        self._rpm_max = rpm_max
        self._redline = rpm_max - 500
        self._rpm_idle = rpm_idle
        self._rpm = 0

        self._car = car

        self._ACCELERATION_CONSTANT = 272
        if sport:
            self._ACCELERATION_CONSTANT = 348

        self._transmission = None
        self._running = False
        self._destroyed = False

    @property
    def running(self):
        return self._running

    @property
    def rpm(self):
        return self._rpm

    def connect_transmission(self, transmission):
        self._transmission = transmission

    def _engine_checks(func, *args, **kwargs):
        def wrap(self, *args, **kwargs):
            if not self._transmission:
                raise Engine.NoTransmissionError("You must connect the transmission")
            if self._destroyed:
                raise Engine.EngineDestroyedError("You destroyed the engine!")
            if not func.__name__ == "start":
                if not self._running:
                    raise Engine.EngineOffError("The engine is off!")
            func(self, *args, **kwargs) 
            if self._rpm >= self._rpm_max:
                raise Engine.EngineDestroyedError("You destroyed the engine!")
                self._running = False
                self._destroyed = True
            if self._rpm >= self._redline:
                raise Engine.EngineRedlineError("You are redlining the engine!")
        return wrap

    @_engine_checks
    def _transmission_sync(self):
        self._rpm = self._transmission.ratio * self._car.speed

    @_engine_checks
    def increase(self):
        self._rpm += self._ACCELERATION_CONSTANT

    @_engine_checks
    def decrease(self):
        self._rpm -= self._ACCELERATION_CONSTANT

    @_engine_checks
    def start(self):
        self._rpm = self._rpm_idle
        self._running = True

    @_engine_checks
    def stop(self):
        self._rpm = 0
        self._running = False


class Transmission(TransmissionBase):
    class TransmissionError(Exception): pass
    class ClutchEngagedError(TransmissionError): pass
    class GearNotFoundError(TransmissionError): pass
    class TransmissionConfigurationError(TransmissionError): pass

    def __init__(self, engine: Engine, gears = None, ratios = None, final_drive = None):
        if not gears:
            self._gears = ("R", "N", "1", "2", "3")
        else:
            self._gears = gears
        if not ratios:
            self._ratios = (-1/3.0, 0, 1/1.86, 1/1.45, 1/1.2)
        else:
            self._ratios = ratios
        if not len(self._gears) == len(self._ratios):
            raise Transmission.TransmissionConfigurationError(f"{self._gears} does not match {self._ratios}")

        self._ratio_map = {k:v for k, v in zip(self._gears, self._ratios)}

        if not final_drive:
            self._final_drive = 1 / 11
        else:
            self._final_drive = final_drive

        self._gear = "N"

        self._engine = engine
        self._engaged = True

    @property
    def ratio(self):
        return self._ratio_map[self.gear] * self._final_drive

    @property
    def gear(self):
        return self._gear

    @property
    def gears(self):
        return self._gears

    @property
    def engaged(self):
        return self._engaged

    def clutch_in(self):
        self._engaged = False

    def clutch_out(self):
        self._engine._transmission_sync()
        self._engaged = True

    def shift_to(self, gear):
        if self.engaged:
            raise Transmission.ClutchEngagedError("You must disengage the clutch!")
        if self.gear not in self.gears:
            raise Transmission.GearNotFoundError(f"There is no gear {gear}!")
        self._gear = gear


class GenericEngine(Engine):
    def __init__(self, car):
        super().__init__(car, 5500, 550)


class SportEngine(Engine):
    def __init__(self, car):
        super().__init__(car, 7800, 625)


class AutomaticTransmission(Transmission):
    class AutomaticTransmissionError(Transmission.TransmissionError): pass
    class NoEngineConnectionError(AutomaticTransmissionError): pass
    class EngineOffError(AutomaticTransmissionError): pass

    def __init__(self, engine):
        self._engine = engine
        super().__init__(engine)

        self._lower_threshold = 750
        self._upper_threshold = 3200

    def _prev_gear(self):
        for i in range(len(self.gears)):
            if self.gears[i] == self.gear:
                break
        return self.gears[i-1]

    def _next_gear(self):
        for i in range(len(self.gears)):
            if self.gears[i] == self.gear:
                break
        return self.gears[i+1]

    # we aren't handling the case where we are out of gears
    # this will throw indexoutofbounds

    def auto_shift(self):
        if not self._engine.running:
            raise AutomaticTransmission.EngineOffError("The engine is off!")
        if self._engine.rpm < self._lower_threshold:
            self.clutch_in()
            self.shift_to(self._prev_gear())
            self.clutch_out()
        if self._engine.rpm > self._upper_threshold:
            self.clutch_in()
            self.shift_to(self._next_gear())
            self.clutch_out()


class SportTransmission(Transmission):
    def __init__(self, engine):
        super().__init__(
            engine,
            ("R", "N", "1", "2", "3", "4", "5"),
            (-1/3.0, 0, 1/1.95, 1/1.73, 1/1.55, 1/1.25, 1/1.0),
            1/9.75,
        )


class Car(CarBase):
    def __init__(self, engine: Engine = None, transmission: Transmission = None):
        if not engine:
            self._engine = GenericEngine(self)
        if not transmission:
            self._transmission = AutomaticTransmission(self._engine)
        self._engine.connect_transmission(self._transmission)
        # 225/70R16
        self._tire_size = 721.4
        self._speed = 0

    @property
    def speed(self):
        return (self._transmission.ratio * self._engine.rpm * 3.14149 * self._tire_size)/1000000

    def _stat_report(func, *args, **kwargs):
        def wrap(self, *args, **kwargs):
            func(self, *args, **kwargs)
            print(self.stats)
        return wrap

    @_stat_report
    def start_car(self):
        self._engine.start()

    @_stat_report
    def accelerate(self):
        if type(self._transmission) is AutomaticTransmission:
            self._transmission.auto_shift()
        try:
            self._engine.increase()
        except Engine.EngineRedlineError:
            print("WARNING: The engine is in redline!")
            raise

    @_stat_report
    def decelerate(self):
        if type(self._transmission) is AutomaticTransmission:
            self._transmission.auto_shift()
        self._engine.decrease()

    @_stat_report
    def shift(self, gear):
        self._transmission.shift_to(gear)

    @property
    def stats(self):
        return f"""Engine: {self._engine.rpm:.0f}
Transmission: {self._transmission.gear}
Ratio: {self._transmission.ratio:.2f}
Speed: {self.speed:.2f}
"""

class ManualCar(Car):
    def __init__(self):
        self._engine = SportEngine(self)
        self._transmission = SportTransmission(self._engine)
        super().__init__(self._engine, self._transmission)

    def clutch_in(self):
        self._transmission.clutch_in()

    def clutch_out(self):
        self._transmission.clutch_out()
