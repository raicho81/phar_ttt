import collections
import functools


class Dependency:
    def __init__(self, class_name, args=(), kwargs={}):
        self._class_name = class_name
        self._args = args
        self._kwargs = kwargs

    @property
    def class_name(self):
        return self._class_name

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def singleton(self):
        return self._singleton


class DependencyInjection:
    DependencyEntry = collections.namedtuple("DependencyEntry", ["singleton", "default_args", "default_kwargs"])
    deps = {}
    singletons = {}

    @staticmethod
    def add_dependency(class_name, *, default_args=(), default_kwargs={}, singleton=False):
        DependencyInjection.deps[class_name] = DependencyInjection.DependencyEntry(singleton, default_args=default_args, default_kwargs=default_kwargs)

    @staticmethod
    def make_args(args, default_args):
        ret_args =  args if args is not None and len(args) > 0 else default_args
        return ret_args

    @staticmethod
    def make_kwargs(kwargs, default_kwargs):
        ret_kwargs =  kwargs if kwargs is not None and len(kwargs) > 0 else default_kwargs
        return ret_kwargs

    @staticmethod
    def get_instance(dep, args=(), kwargs={}):
        depentry = DependencyInjection.deps.get(dep)
        if depentry is None:
            raise ValueError("Unknown Dependency!")
        xx_args = DependencyInjection.make_args(args, depentry.default_args)
        xx_kwargs = DependencyInjection.make_kwargs(kwargs, depentry.default_kwargs)
        if depentry.singleton:
            instance = DependencyInjection.singletons.get(dep)
            if instance:
                return instance
            else:
                DependencyInjection.singletons[dep] = dep(*xx_args, **xx_kwargs)
                return DependencyInjection.singletons[dep]
        return dep(*xx_args, **xx_kwargs)

    @staticmethod
    def inject(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for var_name, var in kwargs.items():
                if isinstance(var, Dependency):
                    for dep in DependencyInjection.deps.keys():
                        if var.class_name is dep.__base__:
                            kwargs[var_name] = DependencyInjection.get_instance(dep, var.args, var.kwargs)
            if f.__kwdefaults__ is not None:
                for var_name, var in f.__kwdefaults__.items():
                    if isinstance(var, Dependency):
                        for dep in DependencyInjection.deps.keys():
                            if var.class_name is dep.__base__:
                                kwargs[var_name] = DependencyInjection.get_instance(dep, var.args, var.kwargs)
            for arg in args:
                if isinstance(arg, Dependency):
                    for dep in DependencyInjection.deps.keys():
                        if arg.class_name is dep.__base__:
                            args[args.index(arg)] = DependencyInjection.get_instance(dep, arg.args, arg.kwargs)
            if f.__defaults__ is not None:
                defaults = list(f.__defaults__)
                for arg in f.__defaults__:
                    if isinstance(arg, Dependency):
                        for dep in DependencyInjection.deps.keys():
                            if arg.class_name is dep.__base__:
                                defaults[defaults.index(arg)] = DependencyInjection.get_instance(dep, arg.args, arg.kwargs)
                f.__defaults__ = tuple(defaults)
            f(*args, **kwargs)
        return wrapper
