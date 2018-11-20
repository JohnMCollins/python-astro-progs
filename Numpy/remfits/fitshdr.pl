#! /usr/bin/perl

# @Author: John M Collins <jmc>
# @Date:   2018-10-02T22:43:34+01:00
# @Email:  jmc@toad.me.uk
# @Filename: fitshdr.pl
# @Last modified by:   jmc
# @Last modified time: 2018-10-04T12:32:13+01:00

use Astro::FITS::CFITSIO;
#use Astro::FITS::CFITSIO qw( :longnames );
#use Astro::FITS::CFITSIO qw( :shortnames );
#use Astro::FITS::CFITSIO qw( :constants );

$ffile = shift @ARGV;
die "No file" unless $ffile;

my $status = 0;
my $fptr = Astro::FITS::CFITSIO::open_file($ffile, Astro::FITS::CFITSIO::READONLY(),$status);
$hash_ref = $fptr->read_header();

for my $k (sort keys %$hash_ref)  {
    print "$k: $hash_ref->{$k}\n";
}
$fptr->close_file($status);
