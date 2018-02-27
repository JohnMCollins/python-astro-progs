#! /usr/bin/perl

use dbops;
use Getopt::Long;

my $year;
my $month;
my $filter;
my $type;
my $outfile;

GetOptions("year=i" => \$year, "month=i" => \$month, "filter=s", \$filter, "type=s" => \$type, "outfile=s" => \$outfile);

unless ($year)  {
    print STDERR "No year given\n";
    exit 10;
}

unless ($month)  {
    print STDERR "No month given\n";
    exit 11;
}

unless ($filter)  {
    print STDERR "No filter given\n";
    exit 12;
}

unless ($type)  {
    print STDERR "No type given\n";
    exit 13;
}

unless ($filter =~ /^[griz]$/)  {
    print STDERR "Unknown filter type $filter\n";
    exit 14;
}

unless ($type =~ /^([fb])/)  {
    print STDERR "Unknown file type $type\n";
    exit 15;
}

unless ($outfile) {
    print STDERR "No output file given\n";
    exit 16;
}

$type = lc $1;
if ($type eq 'f') {
    $type = 'flat';
}
else {
    $type = 'bias';
}

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";
my $sfh = $dbase->prepare("SELECT fitsgz FROM forb WHERE year=$year AND month=$month AND typ='$type' AND filter='$filter'");
$sfh->execute;
my $row = $sfh->fetchrow_arrayref;

unless ($row)  {
    print STDERR "Cannot find specified $type file\n";
    exit 20;
}

my $fits = $row->[0];

open(OUTF, ">$outfile") or die "Cannot create output file $outfile";
my $offs = 0;
my $nbytes = length $fits;
while ($nbytes > 0)  {
    my $nout = 4096;
    $nout = $nbytes if $nout > $nbytes;
    my $nput = syswrite OUTF, $fits, $nout, $offs;
    $offs += $nput;
    $nbytes -= $nput;
}
close OUTF;
exit 0;
