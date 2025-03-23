from conductor.parameter import ConductorParameter

#MM 20241125
#to avoid opening multiple connections to the same device, this is a placeholder, and all phasesetting action happens in cav_eom_amp_sg380
#n.b. device handles phase wrapping (mod 360), NOT handled in software, so phase winding (i.e. setting 370) might cause errors

class CavEomSg380Phase(ConductorParameter):
    autostart = True
    priority = 1
   
    
    def initialize(self, config):
        super(CavEomSg380Phase, self).initialize(config)
        self.connect_to_labrad()
        
    def update(self):
    	pass
        #print(self.value)
 
    
Parameter = CavEomSg380Phase
