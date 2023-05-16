class Engine:
    class EngineError(Exception): pass
    class EngineOffError(EngineError): pass
    class EngineRedlineError(EngineError): pass
    class EngineDestroyedError(EngineError): pass

    def __init__(self, car: Car, transmission: Transmission, rpm_max, rpm_idle, sport=False):
        self._rpm_max = rpm_max
        self._redline = rpm_max - 500
        self._rpm_idle = rpm_idle
        self._rpm = 0

        self._transmission = transmission
        self._car = car

        self._ACCELERATION_CONSTANT = 272
        if sport:
            self._ACCELERATION_CONSTANT = 348

        self._running = False
        self._destroyed = True

    @property
    def rpm(self):
        return self._rpm

    def _engine_checks(func, *args, **kwargs):
        def wrap(self, *args, **kwargs):
            if self._destroyed:
                raise EngineDestroyedError("You destroyed the engine!")
            breakpoint()
            if not func == "start":
                if not self._running:
                    raise EngineOffError("The engine is off!")
            func(self, *args, **kwargs) 
            if self._rpm >= self._redline:
                raise EngineRedlineError("You are redlining the engine!")
            if self._rpm >= self._rpm_max:
                raise EngineDestroyedError("You destroyed the engine!")
                self._running = False
                self._destroyed = True
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


class Transmission:
    class TransmissionError(Exception): pass
    class ClutchEngagedError(TransmissionError): pass
    class GearNotFoundError(TransmissionError): pass

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
            raise TransmissionConfigurationError(f"{self._gears} does not match {self._ratios}")

        self._ratio_map = zip(self._gears, self._ratios)

        if not final_drive:
            self._final_drive = final_drive
        else:
            self._final_drive = 0.12

        self._gear = "N"

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
        if self.engaged():
            raise ClutchEngagedError("You must disengage the clutch!")
        if self.gear not in self.gears:
            raise GearNotFoundError(f"There is no gear {gear}!")
        self._gear = gear


class GenericEngine(Engine):
    def __init__(self):
        super().__init__(5500, 550)


class SportEngine(Engine):
    def __init__(self):
        super().__init__(7800, 625)


class AutomaticTransmission(Transmission):
    class AutomaticTransmissionError(TransmissionError): pass
    class NoEngineConnectionError(AutomaticTransmissionError): pass

    def __init__(self, engine):
        self._engine = engine
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
        if self._engine.rpm < self._lower_threshold:
            self.shift_to(self._prev_gear())
        if self._engine.rpm > self._upper_threshold:
            self.shift_to(self._next_gear())


class SportTransmission(Transmission):
    def __init__(self):
        super().__init__(
            ("R", "N", "1", "2", "3", "4", "5"),
            (-1/3.0, 0, 1/1.95, 1/1.73, 1/1.55, 1/1.25, 1/1.0),
            0.15,
        )


class Car:
    def __init__(self, engine: Engine = None, transmission: Transmission = None):
        if not engine:
            self._engine = GenericEngine()
        if not transmission:
            self._transmission = AutomaticTransmission()
        self._tire_size = 200
        self._speed = 0

    @property
    def speed(self):
        return self._transmission.ratio * self._engine.speed * 3.14149 * self._tire_size

    def start_car(self):
        self._engine.start()

    def accelerate(self):
        self._engine.increase()

    def decelerate(self):
        self._engine.increase()

    def shift(self):
        self._transmission.auto_shift()

    @property
    def stats(self):
        print(f"""
Engine: {self._engine.rpm}
Transmission: {self._transmission.gear}
Ratio: {self._transmission.ratio}
Speed: {self.speed}
""")
