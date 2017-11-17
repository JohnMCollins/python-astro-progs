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
}
