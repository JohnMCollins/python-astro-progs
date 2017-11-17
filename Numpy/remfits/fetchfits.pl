#! /usr/bin/perl

use dbops;
use Getopt::Long;

my $prefix = "fits";

GetOptions("prefix=s", \$prefix) or die "Usage: $0 [ -prefix=x ] inds";

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

