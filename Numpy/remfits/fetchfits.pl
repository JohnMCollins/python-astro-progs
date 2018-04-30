#! /usr/bin/perl

use dbops;
use Getopt::Long;
use Pod::Usage;

my $prefix = "fits";
my $help;

GetOptions("prefix=s", \$prefix, "help" => \$help) or pod2usage(2);
pod2usage(-exitval => 0, -verbose => 2) if $help;

#if ($help)  {
#    print STDERR <<EOF;
# $0 [--help] [--prefix=string] fitsids

# Files are extracted with given prefix and 3 digit zero-filled numbers.
# Fits ids are given by listobs.
# EOF
#     exit 0;
#}

my $n = 1;
my $dbase = dbops::opendb('remfits') or die "Cannot open DB";

for my $id (@ARGV) {
    my $nid = $id + 0;
    my $sfh = $dbase->prepare("SELECT fitsgz FROM obs WHERE ind=$nid");
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
    my $fn = sprintf "%s%.3d.fits.gz", $prefix, $n;
    $n++;
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
 
=back

=head1 DESCRIPTION

This program takes a sequence of FITS ids stored in the database and copies them to a set of files
in the current directory.

The ids are displayed in the output of listobs.

Output files are generated as fits001.fits.gz onward, change the initial "fits" prefix using the
option.
