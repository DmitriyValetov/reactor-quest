import math


def test(index, reactor):
    pass

# def tip(reactor):
#     reactor.acc += 1

def iodine(index, reactor):
  delta_state = 20
  delta_step = 10
  start_step = reactor.events_state[index]
  end_step = start_step + delta_step
  start_state = reactor.ss[start_step]
  end_state = start_state - delta_state
  cur_step = reactor.cur_step
  # Implementation
  # reactor.state += 10
  # reactor.chance += 0.01


# def boron(index, reactor):
#   delta_state = 20
#   delta_step = 10
#   start_step = reactor.events_state[index]
#   end_step = start_step + delta_step
#   start_state = reactor.ss[start_step]
#   end_state = start_state - delta_state
#   cur_step = reactor.cur_step
#   # Implementation
#   reactor.state += 10
#   reactor.chance += 0.01

# def pump_down(reactor):
#     reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})

# def pump_up(reactor):
#     reactor.queue.append({'name': 'water', 'work': 1, 'source': 'reactor'})

# def pump_break(reactor):
#     reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})

# def pump_blow_up(reactor):
#     reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})

# def bribe_chief_engineer(reactor):
#     reactor.queue.append({'name': 'rod_up', 'work': 1, 'source': 'reactor'})

# def press_operators(reactor):
#     reactor.queue.append({'name': 'rod_up', 'work': 1, 'source': 'reactor'})

# def fire(reactor):
#     reactor.queue.append({'name': 'pump_down', 'work': 1, 'source': 'reactor'})

# def rod_down(reactor):
#     reactor.acc -= 1

# def rod_up(reactor):
#     reactor.acc += 1


def rod_up(index, reactor):
  delta_state = 5
  delta_step = 5
  cur_step = reactor.cur_step
  start_step = reactor.events_state[index]
  end_step = start_step + delta_step
  local_step = cur_step - start_step
  start_state = reactor.ss[start_step]
  end_state = start_state + delta_state
  if local_step <= delta_step:
    prev_local_step = local_step - 1 if local_step > 0 else 0
    cur = delta_state*math.exp(local_step/delta_step)
    prev = delta_state*math.exp(prev_local_step/delta_step)
    d = cur - prev
    reactor.state += d

def rod_down(index, reactor):
  delta_state = -5
  delta_step = 5
  cur_step = reactor.cur_step
  start_step = reactor.events_state[index]
  end_step = start_step + delta_step
  local_step = cur_step - start_step
  start_state = reactor.ss[start_step]
  end_state = start_state + delta_state
  if local_step <= delta_step:
    prev_local_step = local_step - 1 if local_step > 0 else 0
    cur = delta_state*math.exp(local_step/delta_step)
    prev = delta_state*math.exp(prev_local_step/delta_step)
    d = cur - prev
    reactor.state += d

def pump_break(index, reactor):
  delta_state = 20
  delta_step = 10
  start_step = reactor.events_state[index]
  end_step = start_step + delta_step
  start_state = reactor.ss[start_step]
  end_state = start_state - delta_state
  cur_step = reactor.cur_step
  # Implementation
  # reactor.state += 10
  # reactor.chance += 0.01

def press_operators(index, reactor):
  delta_state = 20
  delta_step = 10
  start_step = reactor.events_state[index]
  end_step = start_step + delta_step
  start_state = reactor.ss[start_step]
  end_state = start_state - delta_state
  cur_step = reactor.cur_step
  if cur_step < end_step:
    # Implementation
    reactor.state += 10
    reactor.chance += 0.01
  else:
    pass



# def water(reactor):
#     reactor.acc -= 1

# def steam(reactor):
#     reactor.acc += 1

# def scram(reactor):
#     reactor.state = 0
#     reactor.rate = 0
#     reactor.acc = 0
#     reactor.scram_cnt += 1
#     reactor.safe_cnt = 0
#     reactor.zero_cnt += 1

def boom(index, reactor):
    reactor.state = 0
    reactor.rate = 0
    # reactor.acc = 0
    reactor.boom_cnt += 1
    reactor.safe_cnt = 0
    reactor.zero_cnt += 1

# def deenergize(reactor):
#     reactor.queue.append({'name': 'pump_down', 'work': 1, 'source': 'reactor'})

# def replace_boron(reactor):
#     reactor.acc += 1

# def anti_terrorist_operation(reactor):
#     reactor.ato_cnt += 1

factory = {
  'rod_up': rod_up,   # поднять стрежни
  'rod_down': rod_down,  # опустить стрежни
  # 'pump_up': pump_up,  # увеличить расход рабочего тела
  # 'pump_down': pump_down,  # уменьшить расход рабочего тела
  'pump_break': pump_break, # сломать насос
  # 'pump_blow_up': pump_blow_up, # взорвавть насос
  # 'steam': steam,  # добавить пар в реактор (косвенное событие)
  # 'water': water,  # добавить воду в реактор (косвенное событие)
  'iodine': iodine, # иодная яма
  # 'deenergize': deenergize,  # обесточить АЭС
  # 'replace_boron': replace_boron,  # заменить бор на топливо
  # 'boron': boron,  # добавить бор в активную зону
  'boom': boom,  # взрыв
  # 'tip': tip,  # концевой эффект
  # 'scram': scram,  # АЗ-5
  # 'bribe_chief_engineer': bribe_chief_engineer,  # подкупить главного инженера
  'press_operators': press_operators, # надавить на персонал АЭС
  # 'anti_terrorist_operation': anti_terrorist_operation,  # антитеррористическая операция
  # 'fire': fire, # пожар
  'test': test  # тест событие (для тестирования)
}

staff_factory = {
  # 'scram': scram,
  'rod_up': rod_up,
  # 'rod_down': rod_down,
  # 'pump_up': pump_up,
  # 'pump_down': pump_down,
  # 'boron': boron
}

terrors_factory = {
#   'pump_break': pump_break,
  # 'pump_blow_up': pump_blow_up,
  # 'replace_boron': replace_boron,
  # 'deenergize': deenergize,
  # 'fire': fire
  'test': test
}

govs_factory = {
  # 'anti_terrorist_operation': anti_terrorist_operation,
  # 'bribe_chief_engineer': bribe_chief_engineer,
#   'press_operators': press_operators,
  # 'tip': tip
    'test': test
}