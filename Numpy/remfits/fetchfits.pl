#! /usr/bin/perl

# @Author: John M Collins <jmc>
# @Date:   2018-08-26T20:52:51+01:00
# @Email:  jmc@toad.me.uk
# @Filename: fetchfits.pl
# @Last modified by:   jmc
# @Last modified time: 2018-10-04T14:10:26+01:00

use dbops;
use remdefaults;
use Getopt::Long;
use Pod::Usage;
use Astro::FITS::CFITSIO;

my $prefix = "fits";
my $suffix = "fits.gz";
my $help;
my $verbose;
my $obsind;
my $iforbind;
my $n = 1;
my $prec = 3;
my $dbname = remdefaults::default_database;

GetOptions("database=s" => \$dbname, "prefix=s" => \$prefix, "suffix=s" => \$suffix,
           "obsind" => \$obsind, "iforbind" => \$iforbind,
            "digits=i" => \$prec, "verbose" => \$verbose, "start=i" => \$n, "help" => \$help) or pod2usage(2);
pod2usage(-exitval => 0, -verbose => 2) if $help;

#if ($help)  {
#    print STDERR <<EOF;
# $0 [--help] [--prefix=string] [--suffix=string] [--digits=n] [--start=n] [--obsind] [--iforbind] fitsids

# Files are extracted with given prefix and suffix and n digit zero-filled numbers.
# n defaults to 3, prefix to fits and suffix to fits.gz
# Numbering starts by the higher of the given number and first unused file name.
# Fits ids are given by listobs.
# Or select obsinds with --obsind or iforbinds with --iforbind
# EOF
#     exit 0;
#

die "Cannot specify both --iforbind and --obsind" if $obsind && $iforbind;

if ($prefix =~ m;(.*)/(.*)$;) {
    chdir $1 or die "Cannot find directory $1";
    $prefix = $2;
}
$nefiles = 0;
for my $ef (glob('*.fits.gz *.fits')) {
    my $status = 0;
    my $fptr = Astro::FITS::CFITSIO::open_file($ef, Astro::FITS::CFITSIO::READONLY(),$status);
    my $hash_ref = $fptr->read_header();
    my $ifn = $hash_ref->{FILENAME};
    $fptr->close_file($status);
    if  ($ifn)  {
        $Efnames{$ifn} = 1;
        $nefiles++;
    }
}

my $selection;
if ($obsind) {
	$selection = "fitsfile.fitsgz FROM obsinf INNER JOIN fitsfile WHERE obsinf.ind=fitsfile.ind AND obsinf.obsind=";
}
elsif ($iforbind) {
	$selection = "fitsfile.fitsgz FROM iforbinf INNER JOIN fitsfile WHERE iforbinf.ind=fitsfile.ind AND iforbinf.iforbind=";
}
else {
	$selection = "fitsgz FROM fitsfile WHERE ind=";
}

my $dbase = dbops::opendb($dbname) or die "Cannot open DB $dbname";

for my $id (@ARGV) {
    my $nid = $id + 0;
    my $sfh = $dbase->prepare("SELECT $selection$nid");
    $sfh->execute;
    my $row = $sfh->fetchrow_arrayref;
    unless ($row) {
        print "Cannot get fitsfile from $id\n";
        next;
    }
    my $fits = $row->[0];
    my $nbytes = length $fits;
    unless  ($nbytes > 0)  {
        print "Fits file $id zero length\n";
        next;
    }
    my $fn;
    do  {
        $fn = sprintf "%s%." . $prec . "d.%s", $prefix, $n++, $suffix;
    } while -f $fn;
    open(OUTF, ">$fn") or die "Cannot create output file $fn";
    my $offs = 0;
    while ($nbytes > 0)  {
        my $nout = 4096;
        $nout = $nbytes if $nout > $nbytes;
        my $nput = syswrite OUTF, $fits, $nout, $offs;
        $offs += $nput;
        $nbytes -= $nput;
    }
    close OUTF;
    if  ($nefiles > 0)  {
        my $status = 0;
        my $fptr = Astro::FITS::CFITSIO::open_file($fn, Astro::FITS::CFITSIO::READONLY(),$status);
        my $hash_ref = $fptr->read_header();
        my $ifn = $hash_ref->{FILENAME};
        $fptr->close_file($status);
        if  ($ifn && defined $Efnames{$ifn})  {
            unlink $fn;
            $n--;
            print "Duplicated $ifn ref ignored\n" if $verbose;
        }
    }
}

__END__

=head1 NAME

fetchfits - - Copy FITS files out of database

=head1 SYNOPSIS

fetchfits [options] fitsid [fitsid ...]


=head1 OPTIONS

=over 8

=item B<-help>

 Print a brief help message and exit.

=item B<-prefix> string

 Specify prefix for file names (default fits).

=item B<-verbose>

 Report on duplicated FITS files not loaded.

=item B<-start> integer

 Specifiy starting number for fits files, default 1.

=back

=head1 DESCRIPTION

This program takes a sequence of FITS ids stored in the database and copies them to a set of files
in the current directory.

The ids are displayed in the output of listobs.

Output files are generated as fits001.fits.gz onward, change the initial "fits" prefix using the
option.

If there are existing FITS files in the directory, these are not loaded again.
