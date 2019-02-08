#!/usr/bin/env python3
from accessoryFunctions.accessoryFunctions import filer, make_path
from vsnp.vsnp_vcf_methods import VCFMethods
from vsnp.vsnp_vcf_run import VCF
from datetime import datetime
import multiprocessing
from glob import glob
import pytest
import shutil
import os

__author__ = 'adamkoziol'

testpath = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.join(testpath, 'files', 'fastq')
dependencypath = os.path.join(os.path.dirname(testpath), 'dependencies')
report_path = os.path.join(filepath, 'reports')
threads = multiprocessing.cpu_count() - 1
# Define the start time
start_time = datetime.now()


def test_import_vsnp():
    with pytest.raises(SystemExit):
        import vsnp.vSNP


def test_invalid_path():
    with pytest.raises(AssertionError):
        assert VCF(path='not_a_real_path',
                   threads=threads)


def test_no_threads():
    with pytest.raises(TypeError):
        assert VCF(path=filepath)


def test_valid_path():
    vcf_object = VCF(path=filepath,
                     threads=threads)
    assert vcf_object


def test_invalid_tilde_path():
    VCF(path='~',
        threads=threads)


def test_empty_filer():
    fileset = filer(filelist=list())
    assert fileset == set()


def test_empty_filer_dict():
    filedict = filer(filelist=list(),
                     returndict=True)
    assert filedict == dict()


def test_normal_filer_dict():
    filedict = filer(filelist=['03-1057_S10_L001_R1_001.fastq.gz', '03-1057_S10_L001_R2_001.fastq.gz',
                               '13-1941_S4_L001_R1_001.fastq.gz', '13-1941_S4_L001_R2_001.fastq.gz'],
                     returndict=True)
    assert [file_name for file_name in filedict] == ['03-1057', '13-1941']


def test_normal_filer():
    fileset = filer(filelist=['03-1057_S10_L001_R1_001.fastq.gz', '03-1057_S10_L001_R2_001.fastq.gz',
                              '13-1941_S4_L001_R1_001.fastq.gz', '13-1941_S4_L001_R2_001.fastq.gz'])
    assert fileset == {'03-1057', '13-1941'}


def test_missing_file_filer():
    fileset = filer(filelist=['03-1057_S10_L001_R1_001.fastq.gz', '03-1057_S10_L001_R2_001.fastq.gz',
                              '13-1941_S4_L001_R1_001.fastq.gz'])
    assert fileset == {'03-1057', '13-1941'}


def test_non_illumina_filer():
    fileset = filer(filelist=['03-1057_R1.fastq.gz', '03-1057_R2.fastq.gz',
                              '13-1941_R1.fastq.gz', '13-1941_R2.fastq.gz'])
    assert fileset == {'03-1057', '13-1941'}


def test_multiple_differences_filer():
    fileset = filer(filelist=['03-1057_1.fastq', '03-1057_2.fastq',
                              '13-1941_1.fastq.gz', '13-1941_2.fastq'])
    assert fileset == {'03-1057', '13-1941'}


def test_no_directions_filer():
    fileset = filer(filelist=['03-1057.fastq.gz', '13-1941_S4_L001.fastq'])
    assert fileset == {'03-1057', '13-1941'}


def test_vcf_file_list_no_files():
    with pytest.raises(AssertionError):
        VCFMethods.file_list(path=testpath)


def test_vcf_file_list():
    global file_list
    file_list = VCFMethods.file_list(path=filepath)
    assert len(file_list) == 5


def test_strain_dict():
    global strain_folder_dict
    strain_folder_dict = VCFMethods.strain_list(fastq_files=file_list)
    for strain_folder, fastq_files in strain_folder_dict.items():
        if '13-1941' in strain_folder:
            assert len(fastq_files) == 1
        else:
            assert len(fastq_files) == 2


def test_strain_namer_no_input():
    strain_names = VCFMethods.strain_namer(strain_folders=str())
    assert len(strain_names) == 0


def test_strain_namer_working():
    global strain_name_dict
    strain_name_dict = VCFMethods.strain_namer(strain_folders=strain_folder_dict)
    assert [strain for strain in strain_name_dict] == ['13-1941', '13-1950', 'B13-0234']


def test_make_path():
    global make_path_folder
    make_path_folder = os.path.join(testpath, 'test_folder')
    make_path(make_path_folder)
    assert os.path.isdir(make_path_folder)


def test_rm_path():
    os.rmdir(make_path_folder)
    assert os.path.isdir(make_path_folder) is False


def test_strain_linker():
    global strain_fastq_dict
    strain_fastq_dict = VCFMethods.file_link(strain_folder_dict=strain_folder_dict,
                                             strain_name_dict=strain_name_dict)
    assert [strain for strain in strain_fastq_dict] == ['13-1941', '13-1950', 'B13-0234']
    for strain_name, fastq_files in strain_fastq_dict.items():
        if strain_name == '13-1941':
            assert len(fastq_files) == 1
        else:
            assert len(fastq_files) == 2
        for symlink in fastq_files:
            assert os.path.islink(symlink)


def test_reformat_quality():
    global logfile, strain_qhist_dict, strain_lhist_dict
    logfile = os.path.join(filepath, 'log')
    strain_qhist_dict, strain_lhist_dict = VCFMethods.run_reformat_reads(strain_fastq_dict=strain_fastq_dict,
                                                                         strain_name_dict=strain_name_dict,
                                                                         logfile=logfile)
    for strain_name, qhist_paths in strain_qhist_dict.items():
        for strain_qhist_file in qhist_paths:
            assert os.path.basename(strain_qhist_file).startswith(strain_name)
            assert strain_qhist_file.endswith('_qchist.csv')


def test_parse_reformat_quality():
    global strain_average_quality_dict, strain_qual_over_thirty_dict
    strain_average_quality_dict, strain_qual_over_thirty_dict = VCFMethods. \
        parse_quality_histogram(strain_qhist_dict=strain_qhist_dict)
    assert strain_average_quality_dict['13-1950'] == [33.82559209616877, 28.64100810052621]
    assert strain_qual_over_thirty_dict['13-1950'] == [84.5724480421427, 61.085547466494404]


def test_parse_reformat_length():
    global strain_avg_read_lengths
    strain_avg_read_lengths = VCFMethods.parse_length_histograms(strain_lhist_dict=strain_lhist_dict)
    assert strain_avg_read_lengths['13-1950'] == 230.9919625


def test_file_size():
    global strain_fastq_size_dict
    strain_fastq_size_dict = VCFMethods.find_fastq_size(strain_fastq_dict)
    assert strain_fastq_size_dict['13-1950'] == [32.82019233703613, 37.25274848937988]


def test_mash_sketch():
    global fastq_sketch_dict
    fastq_sketch_dict = VCFMethods.call_mash_sketch(strain_fastq_dict=strain_fastq_dict,
                                                    strain_name_dict=strain_name_dict,
                                                    logfile=logfile)
    for strain, sketch_file in fastq_sketch_dict.items():
        assert os.path.isfile(sketch_file)


def test_mash_dist():
    global mash_dist_dict
    mash_dist_dict = VCFMethods.call_mash_dist(strain_fastq_dict=strain_fastq_dict,
                                               strain_name_dict=strain_name_dict,
                                               fastq_sketch_dict=fastq_sketch_dict,
                                               ref_sketch_file=os.path.join(
                                                   dependencypath, 'mash', 'vsnp_reference.msh'),
                                               logfile=logfile)
    for strain, tab_output in mash_dist_dict.items():
        assert os.path.isfile(tab_output)


def test_mash_accession_species():
    global accession_species_dict
    accession_species_dict = VCFMethods.parse_mash_accession_species(mash_species_file=os.path.join(
        dependencypath, 'mash', 'species_accessions.csv'))
    assert accession_species_dict['NC_002945v4.fasta'] == 'af'


def test_mash_best_ref():
    global strain_best_ref_dict, strain_ref_matches_dict, strain_species_dict
    strain_best_ref_dict, strain_ref_matches_dict, strain_species_dict = \
        VCFMethods.mash_best_ref(mash_dist_dict=mash_dist_dict,
                                 accession_species_dict=accession_species_dict)
    assert strain_best_ref_dict['13-1950'] == 'NC_002945v4.fasta'
    assert strain_ref_matches_dict['13-1950'] == 916
    assert strain_species_dict['13-1950'] == 'af'


def test_reference_file_paths():
    global reference_link_path_dict, reference_link_dict
    reference_link_path_dict, reference_link_dict = VCFMethods.reference_folder(
        strain_best_ref_dict=strain_best_ref_dict,
        dependency_path=dependencypath)
    assert reference_link_path_dict['13-1950'] == 'mycobacterium/tbc/af2122/script_dependents/NC_002945v4.fasta'


def test_bowtie2_build():
    global strain_bowtie2_index_dict, strain_reference_abs_path_dict, strain_reference_dep_path_dict
    strain_bowtie2_index_dict, strain_reference_abs_path_dict, strain_reference_dep_path_dict = \
        VCFMethods.bowtie2_build(reference_link_path_dict=reference_link_path_dict,
                                 dependency_path=dependencypath,
                                 logfile=logfile)
    assert os.path.isfile(os.path.join(dependencypath, 'mycobacterium', 'tbc', 'af2122', 'script_dependents',
                                       'NC_002945v4.1.bt2'))
    assert os.path.split(strain_bowtie2_index_dict['13-1950'])[-1] == 'NC_002945v4'


def test_bowtie2_map():
    global strain_sorted_bam_dict
    strain_sorted_bam_dict = VCFMethods.bowtie2_map(strain_fastq_dict=strain_fastq_dict,
                                                    strain_name_dict=strain_name_dict,
                                                    strain_bowtie2_index_dict=strain_bowtie2_index_dict,
                                                    threads=threads,
                                                    logfile=logfile)
    for strain_name, sorted_bam in strain_sorted_bam_dict.items():
        assert os.path.isfile(sorted_bam)


def test_unmapped_reads_extract():
    global strain_unmapped_reads_dict
    strain_unmapped_reads_dict = VCFMethods.extract_unmapped_reads(strain_sorted_bam_dict=strain_sorted_bam_dict,
                                                                   strain_name_dict=strain_name_dict,
                                                                   threads=threads,
                                                                   logfile=logfile)
    for strain_name, unmapped_reads_fastq in strain_unmapped_reads_dict.items():
        assert os.path.getsize(unmapped_reads_fastq) > 0


def test_skesa_assembled_unmapped():
    global strain_skesa_output_fasta_dict
    strain_skesa_output_fasta_dict = VCFMethods.assemble_unmapped_reads(
        strain_unmapped_reads_dict=strain_unmapped_reads_dict,
        strain_name_dict=strain_name_dict,
        threads=threads,
        logfile=logfile)
    assert os.path.getsize(strain_skesa_output_fasta_dict['13-1950']) == 0


def test_number_unmapped_contigs():
    global strain_unmapped_contigs_dict
    strain_unmapped_contigs_dict = VCFMethods.assembly_stats(
        strain_skesa_output_fasta_dict=strain_skesa_output_fasta_dict)
    assert strain_unmapped_contigs_dict['13-1950'] == 0


def test_samtools_index():
    VCFMethods.samtools_index(strain_sorted_bam_dict=strain_sorted_bam_dict,
                              strain_name_dict=strain_name_dict,
                              threads=threads,
                              logfile=logfile)
    for strain_name, sorted_bam in strain_sorted_bam_dict.items():
        assert os.path.isfile(sorted_bam + '.bai')


def test_qualimap():
    global strain_qualimap_report_dict
    strain_qualimap_report_dict = VCFMethods.run_qualimap(strain_sorted_bam_dict=strain_sorted_bam_dict,
                                                          strain_name_dict=strain_name_dict,
                                                          logfile=logfile)
    for strain_name, qualimap_report in strain_qualimap_report_dict.items():
        assert os.path.isfile(qualimap_report)


def test_qualimap_parse():
    global strain_qualimap_outputs_dict
    strain_qualimap_outputs_dict = VCFMethods.parse_qualimap(strain_qualimap_report_dict=strain_qualimap_report_dict)
    assert int(strain_qualimap_outputs_dict['13-1950']['MappedReads'].split('(')[0]) >= 370000


def test_regions():
    global strain_ref_regions_dict
    strain_ref_regions_dict = VCFMethods.reference_regions(
        strain_reference_abs_path_dict=strain_reference_abs_path_dict,
        logfile=logfile)
    for strain_name, ref_regions_file in strain_ref_regions_dict.items():
        assert os.path.isfile(ref_regions_file)
        assert os.path.getsize(ref_regions_file) > 0


def test_freebayes():
    """
    Run FreeBayes on a single strain
    """
    global strain_vcf_dict
    reduced_strain_sorted_bam_dict = dict()
    reduced_strain_sorted_bam_dict['13-1941'] = strain_sorted_bam_dict['13-1941']
    strain_vcf_dict = VCFMethods.freebayes(strain_sorted_bam_dict=reduced_strain_sorted_bam_dict,
                                           strain_name_dict=strain_name_dict,
                                           strain_reference_abs_path_dict=strain_reference_abs_path_dict,
                                           strain_ref_regions_dict=strain_ref_regions_dict,
                                           threads=threads,
                                           logfile=logfile)
    for strain_name, vcf_file in strain_vcf_dict.items():
        assert os.path.getsize(vcf_file) > 10000


def test_copy_test_vcf_files():
    """
    Copy VCF files from test folder to supplement the lone FreeBayes-created VCF file. Populate the strain_vcf_dict
    dictionary with these VCF files
    """
    # Set the absolute path of the test folder containing the VCF files
    vcf_test_path = os.path.join(testpath, 'files', 'vcf')
    # Create a list of all the VCF files
    vcf_files = glob(os.path.join(vcf_test_path, '*.vcf'))
    for strain_name, strain_folder in strain_name_dict.items():
        # Set the absolute path of the destination for the VCF file
        freebayes_out_dir = os.path.join(strain_folder, 'freebayes')
        # Create the working directory if necessary
        make_path(freebayes_out_dir)
        # Set the name of the output .vcf file
        vcf_base_name = '{sn}.vcf'.format(sn=strain_name)
        freebayes_out_vcf = os.path.join(freebayes_out_dir, vcf_base_name)
        # Don't try to copy the file if the original exists
        if not os.path.isfile(freebayes_out_vcf):
            for vcf_file in vcf_files:
                if os.path.basename(vcf_file) == vcf_base_name:
                    shutil.copyfile(vcf_file, freebayes_out_vcf)
        # Update the dictionary
        strain_vcf_dict[strain_name] = freebayes_out_vcf
        assert os.path.isfile(freebayes_out_vcf)


def test_parse_vcf():
    global strain_num_high_quality_snps_dict, strain_filtered_vcf_dict
    strain_num_high_quality_snps_dict, strain_filtered_vcf_dict = VCFMethods.parse_vcf(strain_vcf_dict=strain_vcf_dict)
    assert strain_num_high_quality_snps_dict['13-1941'] == 327


def test_copy_vcf_files():
    global vcf_path
    vcf_path = os.path.join(filepath, 'vcf_files')
    VCFMethods.copy_vcf_files(strain_filtered_vcf_dict=strain_filtered_vcf_dict,
                              vcf_path=vcf_path)
    assert os.path.isdir(vcf_path)
    assert len(glob(os.path.join(vcf_path, '*.vcf'))) == 3


def test_spoligo_bait():
    global strain_spoligo_stats_dict
    strain_spoligo_stats_dict = VCFMethods.bait_spoligo(strain_fastq_dict=strain_fastq_dict,
                                                        strain_name_dict=strain_name_dict,
                                                        spoligo_file=os.path.join(dependencypath,
                                                                                  'mycobacterium',
                                                                                  'spacers.fasta'),
                                                        threads=threads,
                                                        logfile=logfile,
                                                        kmer=25)
    for strain_name, spoligo_stats_file in strain_spoligo_stats_dict.items():
        assert os.path.getsize(spoligo_stats_file) > 0


def test_spoligo_parse():
    global strain_binary_code_dict, strain_octal_code_dict, strain_hexadecimal_code_dict
    strain_binary_code_dict, \
        strain_octal_code_dict, \
        strain_hexadecimal_code_dict = \
        VCFMethods.parse_spoligo(strain_spoligo_stats_dict=strain_spoligo_stats_dict)
    assert strain_binary_code_dict['13-1950'] == '1101000000000010111111111111111111111100000'
    assert strain_octal_code_dict['13-1950'] == '640013777777600'
    assert strain_hexadecimal_code_dict['13-1950'] == '68-0-5F-7F-FF-60'


def test_extract_sbcode():
    global strain_sbcode_dict
    strain_sbcode_dict = VCFMethods.extract_sbcode(strain_reference_dep_path_dict=strain_reference_dep_path_dict,
                                                   strain_octal_code_dict=strain_octal_code_dict)
    assert strain_sbcode_dict['13-1950'] == 'SB0145'


def test_brucella_mlst():
    global mlst_report
    VCFMethods.brucella_mlst(seqpath=filepath,
                             mlst_db_path=os.path.join(dependencypath, 'brucella', 'MLST'),
                             logfile=logfile)
    mlst_report = os.path.join(filepath, 'reports', 'mlst.csv')
    assert os.path.getsize(mlst_report) > 100


def test_mlst_parse():
    global strain_mlst_dict
    strain_mlst_dict = VCFMethods.parse_mlst_report(strain_name_dict=strain_name_dict,
                                                    mlst_report=mlst_report)
    assert strain_mlst_dict['13-1950']['sequence_type'] == 'ND'
    assert strain_mlst_dict['13-1950']['matches'] == 'ND'
    assert strain_mlst_dict['B13-0234']['sequence_type'] == '14'
    assert strain_mlst_dict['B13-0234']['matches'] == '9'


def test_report_create():
    global vcf_report
    vcf_report = VCFMethods.create_vcf_report(
        start_time=start_time,
        strain_species_dict=strain_species_dict,
        strain_best_ref_dict=strain_best_ref_dict,
        strain_fastq_size_dict=strain_fastq_size_dict,
        strain_average_quality_dict=strain_average_quality_dict,
        strain_qual_over_thirty_dict=strain_qual_over_thirty_dict,
        strain_qualimap_outputs_dict=strain_qualimap_outputs_dict,
        strain_avg_read_lengths=strain_avg_read_lengths,
        strain_unmapped_contigs_dict=strain_unmapped_contigs_dict,
        strain_num_high_quality_snps_dict=strain_num_high_quality_snps_dict,
        strain_mlst_dict=strain_mlst_dict,
        strain_octal_code_dict=strain_octal_code_dict,
        strain_sbcode_dict=strain_sbcode_dict,
        strain_hexadecimal_code_dict=strain_hexadecimal_code_dict,
        strain_binary_code_dict=strain_binary_code_dict,
        report_path=report_path)
    assert os.path.getsize(vcf_report) > 100


def test_vcf_run():
    vcf_object = VCF(path=filepath,
                     threads=threads)
    vcf_object.main()


def test_remove_bt2_indexes():
    for strain_name, ref_link in reference_link_path_dict.items():
        # Set the absolute path, and strip off the file extension for use in the build call
        ref_abs_path = os.path.dirname(os.path.abspath(os.path.join(dependencypath, ref_link)))
        bt2_files = glob(os.path.join(ref_abs_path, '*.bt2'))
        for bt2_index in bt2_files:
            os.remove(bt2_index)
        bt2_files = glob(os.path.join(ref_abs_path, '*.bt2'))
        assert not bt2_files


def test_remove_regions_file():
    for strain_name, ref_genome in strain_reference_abs_path_dict.items():
        # Set the absolute path of the regions file
        regions_file = ref_genome + '.regions'
        if os.path.isfile(regions_file):
            os.remove(regions_file)
        assert os.path.isfile(regions_file) is False


def test_remove_logs():
    logs = glob(os.path.join(filepath, '*.txt'))
    for log in logs:
        os.remove(log)


def test_remove_mlst_logs():
    logs = glob(os.path.join(dependencypath, 'brucella', 'MLST', '*.log'))
    for log in logs:
        os.remove(log)


def test_remove_reports():
    shutil.rmtree(report_path)


def test_remove_vcf_path():
    shutil.rmtree(vcf_path)


def test_remove_working_dir():
    for strain_name, working_dir in strain_name_dict.items():
        shutil.rmtree(working_dir)