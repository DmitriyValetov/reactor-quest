def state_range(reactor):
    if 50 < reactor.state <= 75:
        reactor.staff_cnt += 1
    elif 75 < reactor.state <= 100:
        reactor.govs_cnt += 1
    elif reactor.state > 100 or reactor.state == 0:
        reactor.terrors_cnt += 1
    else:
        reactor.no_one_cnt += 1


counts_factory = {
    'state_range': state_range,
}
