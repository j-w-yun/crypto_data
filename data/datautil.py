import numpy


def truncate(x, factor, mean=None, std=None):
    x = numpy.reshape(x, [-1])
    if mean is None:
        mean = numpy.mean(x)
    if std is None:
        std = numpy.std(x)
    clip_min = mean - factor * std
    clip_max = mean + factor * std
    y = numpy.clip(x, clip_min, clip_max)
    return y, mean, std


def z_score(x, mean=None, std=None):
    x = numpy.reshape(x, [-1])
    if mean is None:
        mean = numpy.mean(x)
    if std is None:
        std = numpy.std(x)
    y = (x - mean) / std
    return y, mean, std


def log_ratio(x, scale):
    x = numpy.reshape(x, [-1])
    y = x[1:]  # t+1
    y_ = x[:-1]  # t
    y = numpy.log(y / y_) * scale
    return y


def ma(x, window):
    vals = []
    for i in range(len(x)):
        start = i - window + 1
        end = i + 1
        if start < 0:
            vals.append(numpy.mean(x[:window]))
        else:
            vals.append(numpy.mean(x[start:end]))
    return numpy.array(vals)


def ema(x, window):
    x = numpy.reshape(x, [-1])
    weights = numpy.exp(numpy.linspace(-1.0, 0.0, window))
    weights /= weights.sum()
    vals = []
    for i in range(len(x)):
        start = i - window + 1
        end = i + 1
        if start < 0:
            vals.append(x[i])
        else:
            vals.append(numpy.sum(x[start:end] * weights))
    return numpy.array(vals)


def dema(x, window):
    ema_ = ema(x, window)
    dema_ = ema(ema_, window)
    return 2 * ema_ - dema_


def tema(x, window):
    ema_ = ema(x, window)
    dema_ = ema(ema_, window)
    tema_ = ema(dema_, window)
    return 3 * ema_ - 3 * dema_ + tema_


def vol(x, window):
    vals = []
    for i in range(len(x)):
        start = i - window + 1
        end = i + 1
        if start < 0:
            a = x[:window]
            vals.append(numpy.std(a))
        else:
            a = x[start:end]
            vals.append(numpy.std(a))
    return numpy.array(vals)


def rsi(x, window):
    x = numpy.reshape(x, [-1])
    delta = numpy.diff(x)
    d_up, d_down = delta[1:].copy(), delta[1:].copy()
    d_up[d_up < 0] = 0
    d_down[d_down > 0] = 0
    roll_rp = ma(d_up, window)
    roll_down = ma(d_down, window)
    return roll_rp / numpy.abs(roll_down)
