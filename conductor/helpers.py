def sort_by_priority(parameters):
    return sorted([parameter_name for parameter_name in parameters 
                   if parameters[parameter_name].priority is not None],
                   key=lambda x: parameters[x].priority)[::-1]

def get_remaining_points(parameters):
    return max([len(parameter.value_queue) for parameter in parameters.values()])
