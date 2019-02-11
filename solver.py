'''
solver.py
main code for the first case feasible solver
'''

# sol1 format
'''
--bus section
i, v, theta, b
1,1.05999994278,0.0,-5.0
2,1.04499995708,-0.066464908421,0.0
--generator section
i, uid, p, q
1,'1 ',175.294113159,1.8048504591
'''

# sol2 format
'''
--contingency
label
G_1_1
--bus section
i, v, theta, b
1,1.05999994278,0.0,-5.0
2,1.04499995708,-0.0601769089699,0.0
--generator section
i, uid, p, q
1,1 ,0.0,0.0
--delta section
delta
0.0
--contingency
label
L_1_2_BL
--bus section
i, v, theta, b
1,1.05999994278,0.0,-5.0
2,1.04499995708,-0.0601769089699,0.0
--generator section
i, uid, p, q
1,1 ,176.474899292,9.35432052612
--delta section
delta
0.0
'''

# built in imports
import os, sys, shutil, csv

# GOComp modules - this should be visible on the GOComp evaluation system
import data

# modules for this code
#sys.path.append(os.path.normpath('.')) # better way to make this visible?
#import something

class Solver():

    def __init__(self):
        self.data = data.Data()

    def compute_bus_swsh_adm_imag(self):

        swsh_adm_imag_max = {
            r.i:(max(0.0, r.n1 * r.b1) +
                 max(0.0, r.n2 * r.b2) +
                 max(0.0, r.n3 * r.b3) +
                 max(0.0, r.n4 * r.b4) +
                 max(0.0, r.n5 * r.b5) +
                 max(0.0, r.n6 * r.b6) +
                 max(0.0, r.n7 * r.b7) +
                 max(0.0, r.n8 * r.b8))
            for r in self.data.raw.switched_shunts.values()}
        swsh_adm_imag_min = {
            r.i:(min(0.0, r.n1 * r.b1) +
                 min(0.0, r.n2 * r.b2) +
                 min(0.0, r.n3 * r.b3) +
                 min(0.0, r.n4 * r.b4) +
                 min(0.0, r.n5 * r.b5) +
                 min(0.0, r.n6 * r.b6) +
                 min(0.0, r.n7 * r.b7) +
                 min(0.0, r.n8 * r.b8))
            for r in self.data.raw.switched_shunts.values()}
        swsh_adm_imag_init = {
            r.i:(r.binit if r.stat == 1 else 0.0)
            for r in self.data.raw.switched_shunts.values()}
        swsh_adm_imag_feas = {
            r.i:min(swsh_adm_imag_max[r.i],
                    max(swsh_adm_imag_min[r.i],
                        swsh_adm_imag_init[r.i]))
            for r in self.data.raw.switched_shunts.values()}
        #print swsh_adm_imag_feas
        bus_swsh_adm_imag = {r.i:0.0 for r in self.data.raw.buses.values()}
        #print bus_swsh_adm_imag
        bus_swsh_adm_imag.update(swsh_adm_imag_feas)
        #print bus_swsh_adm_imag
        self.bus_swsh_adm_imag = bus_swsh_adm_imag

    def write_sol1_bus_section(self, w):

        w.writerow(['--bus section'])
        w.writerow(['i', 'v', 'theta', 'b'])
        for b in self.data.raw.buses.values():
            vm = min(b.nvhi, max(b.nvlo, b.vm))
            w.writerow([b.i, vm, b.va, self.bus_swsh_adm_imag[b.i]])

    def write_sol1_generator_section(self, w):

        w.writerow(['--generator section'])
        w.writerow(['i', 'uid', 'p', 'q'])
        for g in self.data.raw.generators.values():
            pg = min(g.pt, max(g.pb, g.pg)) if g.stat == 1 else 0.0
            qg = min(g.qt, max(g.qb, g.qg)) if g.stat == 1 else 0.0
            w.writerow([g.i, g.id, pg, qg])

    def write_sol1(self, sol_name):

        with open(sol_name, 'wb') as sol_file:
            w = csv.writer(sol_file, delimiter=",", quotechar="'", quoting=csv.QUOTE_MINIMAL)
            self.compute_bus_swsh_adm_imag()
            self.write_sol1_bus_section(w)
            self.write_sol1_generator_section(w)

    def write_sol2_bus_section(self, w, k):

        w.writerow(['--bus section'])
        w.writerow(['i', 'v', 'theta', 'b'])
        for b in self.data.raw.buses.values():
            vm = min(b.evhi, max(b.evlo, b.vm))
            w.writerow([b.i, vm, b.va, self.bus_swsh_adm_imag[b.i]])

    def write_sol2_generator_section(self, w, k):

        w.writerow(['--generator section'])
        w.writerow(['i', 'uid', 'p', 'q'])
        for g in self.data.raw.generators.values():
            if (g.i, g.id) in [(e.i, e.id) for e in k.generator_out_events]:
                pg = 0.0
                qg = 0.0
            else:
                pg = min(g.pt, max(g.pb, g.pg)) if g.stat == 1 else 0.0
                qg = min(g.qt, max(g.qb, g.qg)) if g.stat == 1 else 0.0
            w.writerow([g.i, g.id, pg, qg])

    def write_sol2_delta_section(self, w, k):

        w.writerow(['--delta section'])
        w.writerow(['delta'])
        w.writerow([0.0])

    def write_sol2_ctg(self, w, k):

        w.writerow(['--contingency'])
        w.writerow(['label'])
        w.writerow([k.label])
        self.write_sol2_bus_section(w, k)
        self.write_sol2_generator_section(w, k)
        self.write_sol2_delta_section(w, k)

    def write_sol2(self, sol_name):

        with open(sol_name, 'wb') as sol_file:
            w = csv.writer(sol_file, delimiter=",", quotechar="'", quoting=csv.QUOTE_MINIMAL)
            self.compute_bus_swsh_adm_imag()
            for k in self.data.con.contingencies.values():
                self.write_sol2_ctg(w, k)

    def read_data(self, raw_name, rop_name, inl_name, con_name):

        print 'reading data files'
        print 'reading raw file: %s' % raw_name
        self.data.raw.read(os.path.normpath(raw_name))
        print 'reading rop file: %s' % rop_name
        self.data.rop.read(os.path.normpath(rop_name))
        print 'reading inl file: %s' % inl_name
        self.data.inl.read(os.path.normpath(inl_name))
        print 'reading con file: %s' % con_name
        self.data.con.read(os.path.normpath(con_name))
        print "buses: %u" % len(self.data.raw.buses)
        print "loads: %u" % len(self.data.raw.loads)
        print "fixed_shunts: %u" % len(self.data.raw.fixed_shunts)
        print "generators: %u" % len(self.data.raw.generators)
        print "nontransformer_branches: %u" % len(self.data.raw.nontransformer_branches)
        print "transformers: %u" % len(self.data.raw.transformers)
        print "areas: %u" % len(self.data.raw.areas)
        print "switched_shunts: %u" % len(self.data.raw.switched_shunts)
        print "generator inl records: %u" % len(self.data.inl.generator_inl_records)
        print "generator dispatch records: %u" % len(self.data.rop.generator_dispatch_records)
        print "active power dispatch records: %u" % len(self.data.rop.active_power_dispatch_records)
        print "piecewise linear cost functions: %u" % len(self.data.rop.piecewise_linear_cost_functions)
        print 'contingencies: %u' % len(self.data.con.contingencies)
