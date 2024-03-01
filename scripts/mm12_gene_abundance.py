'''
mm12_gene_abundance.py
====================================================

:Author:
:Tags: Python

Purpose
-------

The purpose of this script is to estimate the abundance of genes in an MM12 community given
a set of relative abundance estimates for each MM12 member.

Inputs
-------

The first input is a tab separated file that has relative abundance estimates for a set of samples. Rows
are strains and columns are samples::

   +------------+------------+------------+------------+------------+
   | strain     | sample1    | sample2    | sample3    | sample4    |
   +------------+------------+------------+------------+------------+
   | KB1        | 0.33       | 0.20       | 0.80       | 0.70       |
   +------------+------------+------------+------------+------------+
   | YL32       | 0.33       | 0.80       | 0.00       | 0.15       |
   +------------+------------+------------+------------+------------+
   | I46        | 0.33       | 0.00       | 0.20       | 0.15       |
   +------------+------------+------------+------------+------------+


The second input is a directory that contains a file for each strain that contains annotations. Each
annotation file has the form::

  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+
  |  locus_tag    | ftype |  length_bp | gene  |  EC_number  | COG       |   product                           |         
  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+ 
  | LHNLDECA_00001| CDS   | 1368       | alr   |  5.1.1.1    | COG0787   |  Alanine racemase                   |
  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+
  | LHNLDECA_00002| CDS   | 525        |       |             |           |  hypothetical protein               |
  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+
  | LHNLDECA_00003| CDS   | 501        | luxS  |  4.4.1.21   | COG1854   |  S-ribosylhomocysteine lyase        |
  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+
  | LHNLDECA_00004| CDS   | 1080       | hcxA  |  1.1.1.-    | COG0371   |  Hydroxycarboxylate dehydrogenase A |
  +---------------+-------+------------+-------+-------------+-----------+-------------------------------------+


This is an annotation file that is generated by prokka. The name of each file must have a corresponding entry in the relative
abundance for table. In the example above there should be a KB1.tsv, YL32.tsv and I46.tsv file in the specified annotations
directory.


Usage
-----

To run the script 

Example::

   python mm12_gene_abundance.py --relab=rel_abundance.tsv --annotations-dir=anotations --annotation-type=gene --log=gene_abundance.tsv

Type::

   python mm12_gene_abundance.py --help

for command line help.

Outputs
--------

The output of the script is a table that has each gene as a row and each sample as a column. The relationship between the strain that
each gene has come from is not retained in the output file.


Command line options
--------------------

'''

import sys
import cgatcore.experiment as E
import os
import collections
import glob
import pandas as pd

###########################################################
# Classes and functions for use in the script
###########################################################

def read_relab(relab_file):
    '''
    read in data on relative abundance
    of mm12 members
    '''
    sample_dict = collections.defaultdict(dict)
    relab = open(relab_file)
    samples = relab.readline().strip("\n").split("\t")    
    print(samples)    

    sample_dict = collections.defaultdict(dict)
    for line in relab.readlines():
        data = line.strip("\n").split("\t")
        strain = data[0]
        for i in range(1, len(samples)):
            sample_dict[samples[i]][strain] = data[i]
    return(sample_dict)        

###########################################################
###########################################################
###########################################################

class Annotation(object):

    def __init__(self, locus_tag, ftype, length, gene, ec, cog, product):

        self.locus_tag = locus_tag
        self.ftype = ftype
        self.length = length
        self.gene = gene
        self.ec = ec
        self.cog = cog
        self.product = product

        # set unnannotated genes to "unannotated_gene" etc
        if self.gene == "":
            self.gene = "unannotated_gene"

        # some of the genes are multiple
        # for each strain and are denoted by _number
        # get rid of the number associated
        if len(self.gene.split("_")) == 2:
            self.gene = self.gene.split("_")[0]

        if self.ec == "":
            self.ec = "unannotated_ec"
        if self.cog == "":
            self.cog = "unannotated_cog"
        if self.product == "":
            self.product = "unannotated_gene_product"

###########################################################
###########################################################
###########################################################

def build_annotation(infile, annotation_type="gene"):
    '''
    return a dictionary with strain as key and list
    of genes as values. type has to be one of 
    gene, ko or cog
    '''
    assert annotation_type in ["gene", "ko", "cog"], "annotation_type must be one of gene, ko or cog" 

    strain = os.path.basename(infile).replace(".tsv", "")
    annotations = collections.defaultdict(list)
    with open(infile) as inf:
        for line in inf.readlines():
            data = line.strip("\n").split("\t")
            annotation = Annotation(data[0], data[1], data[2], data[3], data[4], data[5], data[6])
            if annotation_type == "gene":
                annotations[strain].append(annotation.gene)
            elif annotation_type == "ko":
                annotations[strain].append(annotation.ec)
            elif annotation_type == "cog":
                annotations[strain].append(annotation.cog)
    return (annotations)

###########################################################
###########################################################
###########################################################

def get_number_of_genes(annotations):
    '''
    get the number of genes from an annotations
    dictionary
    '''
    return (len(list(annotations.values())[0]))

###########################################################
###########################################################
###########################################################

def check_files(relab_file, annotations_dir):
    '''
    check that all of the strains are present
    '''
    relab = open(relab_file)
    annotation_files = [x.replace(".tsv", "") for x in glob.glob(annotations_dir + "/*.tsv")]
    relab.readline()
    for line in relab.readlines():
        data = line.strip("\n").split("\t")
        strain = data[0]
        if strain not in annotation_files:
            E.warn("strain " + strain + " annotation file not found")
            break

###########################################################
# End of classes and functions. Start of main script
###########################################################

def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.ArgumentParser(description=__doc__)

    parser.add_argument("-r", "--relab", dest="relab", type=str,
                        help="supply filel with relative abundances of MM12 members")
    parser.add_argument("-d", "--annotations-dir", dest="annotations_dir", type=str,
                        help="supply directory containing annotation files")
    parser.add_argument("-t", "--annotation-type", dest="annotation_type", type=str, choices=["gene", "ko", "cog"],
                        help="which type of annotation to use: gene, ko or cog")
    parser.add_argument("-o", "--outfile", dest="outfile", type=str,
                        help="where to output the resulting data")


    # add common options (-h/--help, ...) and parse command line
    (args) = E.start(parser, argv=argv)

    # check inputs
    E.info("Checking input files")
    check_files(args.relab, args.annotations_dir)
    E.info("Inputs checked...OK")

    # read relative abundance file
    E.info("Reading relative abundance file...")
    relab = read_relab(args.relab)

    # iterate over the samples in relab
    # and then the strains and calculate
    # gene relative abundance from the
    # annotation file
    
    annotation_files = glob.glob(args.annotations_dir + "/*.tsv")
    
    # final dictionary of relative abundances for each gene
    gene_relabs = collections.defaultdict(dict)

    for sample, strain_relab in relab.items():
        for strain, relab in strain_relab.items():
            E.info("Calculating gene relative abundance for " + sample + " and annotations for " + strain)
            annotation = [x for x in annotation_files if os.path.basename(x).replace(".tsv", "") == strain][0]
            annotation = build_annotation(annotation, annotation_type=args.annotation_type)
            ngenes = get_number_of_genes(annotation)
            
            # the relative abundance of each gene is calculated 
            # as the relative abundance of the organism/mnumber of genes
            for g in list(annotation.values())[0]:
                if g == "gene":
                    continue
                try: 
                  gene_relabs[sample][g] = gene_relabs[sample][g] + float(relab)/float(ngenes)
                except KeyError:
                  gene_relabs[sample][g] = float(relab)/float(ngenes)
    
    # get pandas dataframe for putput
    df = pd.DataFrame(gene_relabs)

    # write table
    df.to_csv(args.outfile, sep="\t", index_label="gene") 

    # write footer and output benchmark information.
    E.stop()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
