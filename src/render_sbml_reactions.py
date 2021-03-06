from __future__ import division
import sys
import os
import itertools
import argparse
import pygraphviz
import chen_2009_original_sbml

def neighbor_set(nodes):
    return set(itertools.chain.from_iterable(graph.neighbors(n) for n in nodes))

def reverse_reaction(reaction, logical=True, visual=True):
    for s in reaction.reactants:
        if s in graph:
            reverse_edge(s, reaction, logical, visual)
    for s in reaction.products:
        if s in graph:
            reverse_edge(reaction, s, logical, visual)

def reverse_edge(u, v, logical, visual):
    e = graph.get_edge(u, v)
    if not logical and not visual:
        raise ValueError("logical and/or visual must be True")
    elif not logical and visual:
        e.attr['dir'] = 'back'
    elif logical:
        attrs = dict(e.attr)
        if not visual:
            attrs['dir'] = 'back'
        graph.add_edge(v, u, **attrs)
        graph.remove_edge(u, v)

cluster_seq = itertools.count()
def add_box(*species_list):
    nodes = [str(s) for s in species_list]
    name = 'cluster_{}'.format(next(cluster_seq))
    cluster = graph.add_subgraph(nodes, name, color='none', bgcolor='gray94')
    globals()[name] = cluster
    if args.debug:
        cluster.graph_attr.update(label=name, fontname='courier bold',
                                  fontsize=18)
    return cluster

def add_group(*cluster_list):
    name = 'cluster_group_{}'.format(next(cluster_seq))
    cluster = graph.add_subgraph([], name, color='none')
    globals()[name] = cluster
    if args.debug:
        cluster.graph_attr.update(label=name, fontname='courier bold',
                                  fontsize=24, color='red', bgcolor='pink')
    for sg in cluster_list:
        cluster.add_nodes_from(sg)
        globals()[sg.name] = cluster.add_subgraph(sg, sg.name, **sg.graph_attr)
        graph.remove_subgraph(sg.name)
    for rxn_node in set(itertools.chain.from_iterable(graph.neighbors_iter(n)
                                                      for n in cluster.nodes())):
        if all(neighbor in cluster for neighbor in graph.neighbors(rxn_node)):
            cluster.add_node(rxn_node)
    return cluster

# All the dark ("4") colors from the graphviz color set.
color_cycle = itertools.cycle((
        'antiquewhite4', 'aquamarine4', 'azure4', 'bisque4', 'blue4', 'brown4',
        'burlywood4', 'cadetblue4', 'chartreuse4', 'chocolate4', 'coral4',
        'cornsilk4', 'cyan4', 'darkgoldenrod4', 'darkolivegreen4',
        'darkorange4', 'darkorchid4', 'darkseagreen4', 'deeppink4',
        'deepskyblue4', 'dodgerblue4', 'firebrick4', 'gold4', 'goldenrod4',
        'green4', 'honeydew4', 'hotpink4', 'indianred4', 'ivory4', 'khaki4',
        'lavenderblush4', 'lemonchiffon4', 'magenta4', 'maroon4',
        'mediumorchid4', 'mediumpurple4', 'mistyrose4', 'navajowhite4',
        'olivedrab4', 'orange4', 'orangered4', 'orchid4', 'peachpuff4', 'pink4',
        'plum4', 'purple4', 'red4', 'rosybrown4', 'royalblue4', 'salmon4',
        'seagreen4', 'seashell4', 'sienna4', 'skyblue4', 'slateblue4', 'snow4',
        'springgreen4', 'steelblue4', 'tan4', 'thistle4', 'tomato4',
        'turquoise4', 'violetred4', 'wheat4', 'yellow4'))



argparser = argparse.ArgumentParser(
    description='Render Chen 2009 SBML model reaction graph.')
argparser.add_argument('-d', '--debug', action='store_true',
                       help="Debug mode (extra visual output)")
# Adding the endosomal receptor degradation reactions adds way too much clutter
# so by default this is off.
argparser.add_argument('--show-r-degraded', action='store_true',
                       help="Show endosomal receptor degradation reactions")
# Removing free adapter proteins simplifies the graph.
argparser.add_argument('--simplify-adapters', action='store_true',
                       help="Hide free adapter proteins")
args = argparser.parse_args()


model = chen_2009_original_sbml.load_model()
model.export_globals()


## Construct graphviz representation of reaction network.

graph = pygraphviz.AGraph(directed=True, rankdir='LR', compound=True,
                          nodesep=0.1, ranksep=1.2, mclimit=10)
graph.node_attr.update(fontname='Helvetica')
graph.edge_attr.update(arrowsize=0.7)
for s in model.species:
    label = '<{0.label} <sup>{0.name}</sup>>'.format(s)
    graph.add_node(s, _type='species', label=label, shape='none',
                   bgcolor='white', margin=0.01, height=0)
for r in model.reactions:
    graph.add_node(r, _type='reaction', label=r.name, shape='none',
                   fontcolor='#13ac4a', width=0, height=0, margin=0.05)
    color = next(color_cycle)
    for reactant in r.reactants:
        graph.add_edge(reactant, r, color=color)
    for product in r.products:
        graph.add_edge(r, product, color=color)

# delete some "nuisance" nodes from the graph
for label in 'ATP',:
    graph.remove_node(model.species_by_label(label))

# Fix reactions that were specified "backwards" in the original model. This
# swaps the direction of all edges on these reaction nodes.
for r in (
    v804, v807, v812, v813, v822, v823, v824, # dimer#P catalysis step
    v825, v814,                               #   (continued)
    v808, v811, v809, v826, v810, v827,       # endo|dimer#P catalysis step
    v657, v658, v659, v660, v661, v662, v663, # endo|dimer#P diss RTK_Pase
    v109, v111, v123, v139, v140, v141, v161, # R.. diss cPP
    v107, v108, v122, v128, v129, v130, v162, # R..Sos diss cPP
    v117, v118, v127, v151, v152, v153, v158, # R..Shc diss cPP
    v110, v116, v126, v148, v149, v150, v157, # R..Shc..Sos diss cPP
    v105, v106, v121, v136, v137, v138, v160, # R..RasGDP diss cPP
    v103, v104, v120, v133, v134, v135, v159, # R..RasGTP diss cPP
    v114, v115, v125, v145, v146, v147, v156, # R..Shc..RasGDP diss cPP
    v112, v113, v124, v142, v143, v144, v155, # R..Shc..RasGTP diss cPP
    v283, v285, v287, v294, v301, v302, v303, # R..RasGDP cat
    v289, v293, v295, v296, v297, v307, v309, # R..Shc..RasGDP cat
    v257, v268, v269, v270, v274, v280, v282, # endo|R..RasGDP cat
    v411, v412,                               # Raf phos
    v495, v496, v497, v498,                   # MEK phos
    v511, v512, v513, v514,                   # ERK phos
    v815, v816, v817, v818, v819, v820, v821, # Gab1 phos
    # The following row would include v764 but one of its reactants is wrong
    # (this is an error in the model).
    v758, v759, v760, v761, v762, v763,       # PI3K..RasGDP cat
    v737, v741, v743, v739, v749, v745, v747, # ERK..Gab1#P cat
    # The following should include a reaction involving c408 (4:2 dimer) but the
    # product species c455 was mislabled and the reaction was omitted.
    v628, v629, v630, v631, v632, v633,       # PIP2 phos (regular)
    v634, v635, v636, v637, v638,             # PIP2 phos (2:3 dimer extra rxns)
    v643, v644,                               # AKT phos
    v767,                                     # Raf#P#Ser cat
    ):
    reverse_reaction(r)
# Fix "retrograde" reactions -- those whose forward direction is logically
# "backward" in the signaling network. This switches the logical edge direction
# without changing the visual appearance (i.e. which end has the arrowhead),
# leading to improved graph layout.
for r in (
    v443,                                     # Shc spontaneous dephos
    v211,                                     # cPP transloc to cytoplasm
    v487, v488,                               # Raf#P bind Pase1
    v505, v506, v499, v500,                   # MEK#P(#P) bind Pase2
    v521, v522, v515, v516,                   # ERK#P(#P) bind Pase3
    v707, v708, v709, v710, v711, v712, v713, # Gab1#P bind Shp2
    v770, v771, v772, v773, v774, v775, v776, # Gab1#P#P bind Pase9t
    v609, v610, v611, v612,                   # R..Sos bind ERK#P#P
    v613, v614,                               # free Sos bind ERK#P#P
    v721, v722,                               # PTEN/Shp bind PIP3
    v646, v645,                               # AKT#P(#P) bind Pase4
    ):
    reverse_reaction(r, visual=False)
# Fix reactions that are backwards AND retrograde. This switches the visual
# appearance without changing the logical direction.
for r in (
    v489, v490,                               # Raf dephos
    v502, v503, v501, v504,                   # MEK dephos
    v519, v520, v517, v518,                   # ERK dephos
    v714, v715, v716, v717, v718, v719, v720, # Gab1#P dephos
    v781, v783, v777, v782, v779, v780, v778, # Gab1#P#P dephos
    v615, v618, v616, v619,                   # R..Sos phos
    v669, v670, v671, v672,                   # R..Grb2 diss Sos#P
    v617, v620,                               # free Sos phos
    v686, v687,                               # PIP3 dephos
    v649,                                     # PDK1 diss PIP3
    v647, v648,                               # AKT#P(#P) dephos
    ):
    reverse_reaction(r, logical=False)

## Plasma membrane receptors and ligands

# single ErbB1
add_box(c531)
# single receptors
add_box(c2, c141, c140, c143)
# 2:3 / 2:4 dimers
add_box(c288, c117)
# ligands
add_box(c1, c514)
# ligand-bound single receptors
add_box(c3, c142, c144)
# ligand-bound receptor dimers, and 2:2#P dimer
add_box(c4, c145, c146, c147, c355, c345, c516, c517, c284)
# ATP-and-ligand-bound receptor dimers, and ATP-bound 2:2#P dimer
add_box(c116, c122, c127, c128, c168, c139, c137, c138, c129)
# Phosphorylated dimers (dimer#P)
add_box(c5, c148, c149, c150, c335, c336, c289)
# Phosphorylated monomers
add_box(c330, c87, c331, c332)

## Adapters

# GAP
add_box(c14)
# dimer#P:GAP
add_box(c341, c344, c291, c15, c151, c152, c153)
# Shc
add_box(c31)
# Grb2
add_box(c22)
# Sos
add_box(c24)
# Shc#P
add_box(c40)
# (Shc#P):Grb2
add_box(c39)
# (Shc#P):Grb2:Sos
add_box(c38)
# Grb2:SOS
add_box(c30)
# dimer#P:GAP:Shc
add_box(c347, c348, c294, c171, c172, c173, c32)
# dimer#P:GAP:(Shc#P)
add_box(c351, c354, c297, c180, c181, c182, c33)
# dimer#P:GAP:(Shc#P):Grb2
add_box(c357, c360, c300, c189, c190, c191, c34)
# dimer#P:GAP:(Shc#P):Grb2:Sos
add_box(c363, c366, c303, c198, c199, c200, c35)
# dimer#P:GAP:Grb2
add_box(c381, c384, c312, c225, c226, c227, c23)
# dimer:P:GAP:Grb2:Sos
add_box(c387, c390, c315, c234, c235, c236, c25)

## Endosome receptors and ligands

# single receptors
add_box(c156, c154, c155, c6)
# 2:2 / 2:3 / 2:4 dimers
add_box(c425, c339, c340)
# ligands
add_box(c16, c515)
# degraded EGF
add_box(c13)
# ligand-bound single receptors
add_box(c10, c157, c158)
# ligand-bound receptor dimers
add_box(c11, c159, c160, c161, c421, c422, c518, c519)
# ATP-and-ligand-bound receptor dimers
add_box(c126, c123, c124, c125, c169, c170)
# Phosphorylated dimers (dimer#P)
add_box(c8, c162, c163, c164, c337, c338, c290)

## RTK phosphatase

# RTK Phosphatase
add_box(c280)
# dimer#P:Phosphatase
add_box(c415, c416, c281, c283, c282, c417, c418)

## Endosome adapters

# dimer#P:GAP
add_box(c343, c346, c293, c17, c165, c166, c167)
# dimer#P:GAP:Shc
add_box(c349, c350, c296, c174, c175, c176, c63)
# dimer#P:GAP:(Shc#P)
add_box(c353, c356, c299, c183, c184, c185, c64)
# dimer#P:GAP:(Shc#P):Grb2
add_box(c359, c362, c302, c192, c193, c194, c65)
# dimer#P:GAP:(Shc#P):Grb2:Sos
add_box(c365, c368, c305, c201, c202, c203, c66)
# dimer#P:GAP:Grb2
add_box(c383, c386, c314, c228, c229, c230, c18)
# dimer:P:GAP:Grb2:Sos
add_box(c389, c392, c317, c237, c238, c239, c19)

## Coated-pit-protein-bound adapters

# cPP
add_box(c12)
# endo|cPP
add_box(c9)
# dimer#P:GAP:(Shc#P):Grb2
add_box(c358, c361, c301, c195, c196, c197, c91)
# dimer#P:GAP:(Shc#P):Grb2:Sos
add_box(c364, c367, c304, c204, c205, c206, c92)
# dimer#P:GAP:Grb2
add_box(c382, c385, c313, c231, c232, c233, c7)
# dimer:P:GAP:Grb2:Sos
add_box(c388, c391, c316, c240, c241, c242, c88)

## RAS-bound complexes

# Ras:GDP
add_box(c26)
# Ras:GTP
add_box(c28)
# Ras_activated:GTP
add_box(c43)
# Raf:Ras:GTP
add_box(c42)

# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGDP, plasma membrane
add_box(c369, c372, c306, c207, c208, c209, c36)
# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGDP, cpp-bound
add_box(c370, c373, c307, c213, c214, c215, c93)
# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGDP, endosome
add_box(c371, c374, c308, c210, c211, c212, c67)

# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGTP, plasma membrane
add_box(c375, c378, c309, c216, c217, c218, c37)
# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGTP, cpp-bound
add_box(c376, c379, c310, c222, c223, c224, c94)
# dimer#P:GAP:(Shc#P):Grb2:Sos:RasGTP, endosome
add_box(c377, c380, c311, c219, c220, c221, c68)

# dimer#P:GAP:Grb2:Sos:RasGDP, plasma membrane
add_box(c393, c396, c318, c243, c244, c245, c27)
# dimer#P:GAP:Grb2:Sos:RasGDP, cpp-bound
add_box(c394, c397, c319, c249, c250, c251, c89)
# dimer#P:GAP:Grb2:Sos:RasGDP, endosome
add_box(c395, c398, c320, c246, c247, c248, c20)

# dimer#P:GAP:Grb2:Sos:RasGTP, plasma membrane
add_box(c399, c402, c321, c252, c253, c254, c29)
# dimer#P:GAP:Grb2:Sos:RasGTP, cpp-bound
add_box(c400, c403, c322, c258, c259, c260, c90)
# dimer#P:GAP:Grb2:Sos:RasGTP, endosome
add_box(c401, c404, c323, c255, c256, c257, c21)

## MAPK signaling

# Raf
add_box(c41)
# MEK
add_box(c47)
# ERK
add_box(c55)
# Pase1
add_box(c44)
# Pase2
add_box(c53)
# Pase3
add_box(c60)
# Raf#P
add_box(c45)
# Raf#P:Pase1
add_box(c46)
# MEK:Raf#P
add_box(c48)
# MEK#P
add_box(c49)
# MEK#P:Raf#P
add_box(c50)
# MEK#P#P
add_box(c51)
# MEK#P#P:Pase2
add_box(c52)
# MEK#P:Pase2
add_box(c54)

# ERK:MEK#P#P
add_box(c56)
# ERK#P
add_box(c57)
# ERK#P:MEK#P#P
add_box(c58)
# ERK#P#P
# TODO: split these to make the Gab1 second phosphorylation reactions collapse?
add_box(c59)
# ERK#P#P:Pase3
add_box(c61)
# ERK#P:Pase3
add_box(c62)
# MKP_deg (Pase3 degraded)
add_box(c520)

# dimer#P:GAP:Grb2:Sos:ERK#P#P
add_box(c95)
# dimer#P:GAP:(Shc#P):Grb2:Sos:ERK#P#P
add_box(c97)
# dimer#P:GAP:Grb2:Sos#P
add_box(c99, c100)
# dimer#P:GAP:(Shc#P):Grb2:Sos#P
add_box(c419, c420)
# ERK#P#P:Sos
add_box(c101)
# Sos#P
add_box(c103)

##  PI3K signaling

# Gab1
add_box(c426)
# Shp2
add_box(c463)
# PI3K
add_box(c287)
# Pase9t
add_box(c521)
# dimer#P:GAP:Grb2:Gab1
add_box(c442, c439, c436, c427, c428, c429, c483)
# dimer#P:GAP:Grb2:Gab1:ATP
add_box(c130, c131, c132, c133, c134, c135, c136)
# dimer#P:GAP:Grb2:Gab1#P
add_box(c457, c460, c454, c445, c446, c447, c486)
# dimer#P:GAP:Grb2:Gab1#P:Shp2
add_box(c476, c479, c473, c464, c465, c466, c489)
# dimer#P:GAP:Grb2:Gab1#P:ERK#P#P
add_box(c477, c480, c474, c433, c435, c438, c431)
# dimer#P:GAP:Grb2:Gab1#P#P
add_box(c491, c487, c490, c430, c409, c410, c488)
# dimer#P:GAP:Grb2:Gab1#P#P:Pase9t
add_box(c456, c407, c522, c424, c411, c412, c523)
# dimer#P:GAP:Grb2:Gab1#P:PI3K
add_box(c405, c408, c324, c261, c262, c263, c104)
# dimer#P:GAP:Grb2:Gab1#P:PI3K:RasGDP
add_box(c269, c325, c268, c265, c267, c266, c264)

# PIP2
add_box(c444)
# PIP3
add_box(c106)
# dimer#P:GAP:Grb2:Gab1#P:PI3K:PIP2
add_box(c453, c455, c452, c449, c450, c451, c448)
# (ErbB2:ErbB3)#P:GAP:Grb2:Gab1#P:PI3K:PIP2*{2,3,4,5,6}
add_box(c467, c468, c469, c470, c471)

# PTEN, Shp
add_box(c279, c461)
# PIP3:PTEN, PIP3:Shp
add_box(c482, c462)

## AKT signaling

# AKT
add_box(c107)
# PDK1
add_box(c109)
# Pase4
add_box(c113)
# PIP3:AKT
add_box(c108)
# PIP3:AKT:PDK1
add_box(c110)
# PIP3:PDK1
add_box(c111)
# AKT#P
add_box(c112)
# PIP3:AKT#P
add_box(c495)
# PIP3:AKT#P:PDK1
add_box(c496)
# AKT#P#P
add_box(c497)
# AKT#P:Pase4
add_box(c114)
# AKT#P#P:Pase4
add_box(c498)

## AKT negative feedback on Raf

# AKT#P#P:Raf#P#Ser
add_box(c472)
# Raf#P#Ser
add_box(c485)

if args.show_r_degraded:
  #R_degraded
  add_box(c86)

# Delete stuff we haven't explicitly enumerated through add_box calls above.
box_nodes = [n for g in graph.subgraphs() for n in g.nodes()]
box_and_neighbors = set(box_nodes) | neighbor_set(box_nodes)
species_nodes_to_drop = set(
    n for n in graph.nodes_iter()
    if n not in box_and_neighbors and n.attr['_type'] == 'species')
reaction_nodes_to_drop = neighbor_set(species_nodes_to_drop)
dropped_species = [s for s in model.species
                   if s.name in species_nodes_to_drop]
dropped_reactions = [r for r in model.reactions
                     if r.name in reaction_nodes_to_drop]
for n in list(species_nodes_to_drop | reaction_nodes_to_drop):
    graph.remove_node(n)
num_keep_species = len([n for n in graph.nodes() if n.attr['_type'] == 'species'])
num_keep_reactions = len([n for n in graph.nodes() if n.attr['_type'] == 'reaction'])

# Collapse sets of parallel reaction nodes.
node_to_subgraph = {n: g for g in graph.subgraphs() for n in g.nodes()}
rxn_nodes = [n for n in graph.nodes() if n.attr['_type'] == 'reaction']
rxn_cluster_neighbors = [
    tuple(sorted(node_to_subgraph[sn] for sn in graph.neighbors(rn)))
    for rn in rxn_nodes]
rxn_to_cn = dict(zip(rxn_nodes, rxn_cluster_neighbors))
# Sort reaction nodes based on which species subgraphs (clusters) they are
# adjacent to. Map subgraphs to their ids because graph equality in pygraphviz
# is VERY expensive -- it serializes them to strings and compares those!
rxn_nodes.sort(key=lambda r: map(id, rxn_to_cn[r]))
for subgraphs, node_iter in itertools.groupby(rxn_nodes, rxn_to_cn.get):
    nodes = list(node_iter)
    edges = []
    for sg in subgraphs:
        for rn, sn in itertools.product(nodes, sg):
            for u, v in itertools.permutations([rn, sn]):
                try:
                    edges.append(graph.get_edge(u, v))
                except KeyError:
                    continue
    # Necessary conditions for collapsing this set of reaction nodes:
    # 1) There are at least two reactions.
    multiple_rxns = len(nodes) > 1
    # 2) There is a 1:1 connection between every reaction and the species in
    # each neighboring cluster, or the neighboring cluster is of size 1.
    full_coverage = all(
        sum(n.attr['_type'] == 'species' for n in sg) in (1, len(nodes))
        for sg in subgraphs
        )
    # 3) Each edge is going in the same direction (i.e. don't collapse forward
    # and backward reactions involving the exact same species). We probably
    # won't fail this check in a well-built model, but the "dir" attribute
    # preservation below does depend on this condition.
    edges_same_dir = len(set(e.attr['dir'] for e in edges)) == 1
    if (multiple_rxns and full_coverage and edges_same_dir):
        node_id = 'reaction_' + '_'.join(sg.name for sg in subgraphs)
        label = r'\n'.join(sorted(n.attr['label'] for n in nodes))
        graph.add_node(node_id, label=label, fontcolor='#13ac4a', shape='box',
                       width=0, height=0, margin=0.05, color='#13ac4a20',
                       _type='reaction')
        r_nodes = graph.predecessors(nodes[0])
        p_nodes = graph.successors(nodes[0])
        base_edge_attrs = {
            'color': next(color_cycle),
            'dir': edges[0].attr['dir'],
            'weight': len(nodes),
            }
        for ntype, species_nodes in ('reactant', r_nodes), ('product', p_nodes):
            for species_node in species_nodes:
                sg = node_to_subgraph[species_node]
                u, v = sg.nodes_iter().next(), node_id
                if ntype == 'reactant':
                    lheadtail = 'ltail'
                else:
                    lheadtail = 'lhead'
                    u, v = v, u
                attrs = dict(base_edge_attrs)
                if len(sg) > 1:
                    attrs.update({lheadtail: sg.name}, arrowsize=1.4,
                                 style='bold')
                graph.add_edge(u, v, **attrs)
        for n in nodes:
            graph.remove_node(n)


add_group(cluster_5, cluster_6, cluster_7, cluster_8)
add_group(cluster_24, cluster_28, cluster_29, cluster_30, cluster_31,
          cluster_25, cluster_32, cluster_33)


# Remove free adapter proteins to simplify the graph.
if args.simplify_adapters:
    for s in c12, c28, c26, c43, c22, c24, c30, c39, c31, c40, c9, c38, c14:
        graph.remove_node(s)


# Write output to .dot file in same directory as this script.
dot_path = os.path.join(os.path.dirname(__file__), 'chen_2009_original.dot')
graph.write(dot_path)
# Call graphviz to render a PDF.
pdf_path = dot_path.replace('.dot', '.pdf')
os.system("dot {} -Tpdf -o {}".format(dot_path, pdf_path))
print >>sys.stderr, "Output rendered to:", os.path.relpath(pdf_path)


num_total_species = len(model.species)
num_total_reactions = len(model.reactions)
print >>sys.stderr
print >>sys.stderr, ("Species: {} / {} ({}%)"
                     .format(num_keep_species, num_total_species,
                             100 * num_keep_species / num_total_species))
print >>sys.stderr, ("Reactions: {} / {} ({}%)"
                     .format(num_keep_reactions, num_total_reactions,
                             100 * num_keep_reactions / num_total_reactions))
