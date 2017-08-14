#! /usr/bin/perl

$Harps = shift @ARGV;
$Allids = shift @ARGV;
$Stfile = shift @ARGV;
$outfile = shift @ARGV;
$nffile = shift @ARGV;

die "No Harps file" unless defined $Harps;
die "No allids file" unless defined $Allids;
die "No st file" unless defined $Stfile;
die "No out file" unless defined $outfile;
die "No not found file" unless defined $nffile;

chdir "/home/jmc/Downloads";

die "Cannot open Harps file $Harps" unless open(HF, $Harps);
die "Cannot open all ids file $Allids" unless open(ALL, $Allids);
die "Cannot open ST file $Stfile" unless open(ST, $Stfile);

our %Stlookup;

while (<ST>)  {
    chop;
    next unless /^\d+\s+(\S+).*(\d\d)\s+(\d\d)\s+([.\d]+)\s+([-+]?\d+)\s+(\d\d)\s+([.\d]+)(?:\s+[-~.\d]+){4,5}\s+([OBAFGKM]\S+)/;
    my $id = $1;
    my $ra = $2 * 15.0 + $3 / 4.0 + $4 / 240.0;
    my $dec = $5 + 0.0;
    my $decf = $6 / 60.0 + $7 / 3600.0;
    if ($dec < 0.0) {
        $dec -= $decf;
    }
    else {
        $dec += $decf;
    }
    my $st = $8;
    
    $Stlookup{$id} = {ST => $st, SRA => $ra, SDEC => $dec};
}

close ST;

our @idl;

while (<HF>)  {
	chop;
	my ($id, $ra, $dec, $dat, $bl, $idays, $epochs) = split /\s+/;
	my $item = {ID => $id, ALIASID => $id, RA => $ra, DEC => $dec, DAT => $dat, BASELD => $bl, IDAYS => $idays, EPOCHS => $epochs};
	push @idl, $item;
}

close HF;

our @cidl = @idl;

while (<ALL>)  {
    my $cl = shift @cidl;
    chop;
    s/\s+//g;
    my $id = $_;
    if ($id ne $cl->{ID})  {
        print "$cl->{ID} changed to $id\n";
        $cl->{ALIASID} = $id;
    }
}

close ALL;

for my $id (@idl)  {
    my $stf = $Stlookup{$id->{ALIASID}};
    next unless defined $stf;
    for my $k (keys %$stf) {
        $id->{$k} = $stf->{$k};
    }
}

die "Cannot create output" unless open(OUTF, ">$outfile");
die "Cannot create nf file" unless open(NOTF, ">$nffile");

for my $spectype (qw/O B A F G K M/)  {
    for my $id (@idl)  {
        next unless defined $id->{ST} and (substr $id->{ST},0,1) eq $spectype;
        printf OUTF "%s %s %.6f %.6f %.6f %.6f %d %d %d %d\n", $id->{ID}, $id->{ST}, $id->{RA}, $id->{DEC}, $id->{SRA}, $id->{SDEC}, $id->{DAT}, $id->{BASELD}, $id->{IDAYS}, $id->{EPOCHS};
    }
}

for my $id (@idl)  {
    next if defined $id->{ST};
    printf NOTF "%s %.6f %.6f %d %d %d %d\n", $id->{ID}, $id->{RA}, $id->{DEC}, $id->{DAT}, $id->{BASELD}, $id->{IDAYS}, $id->{EPOCHS};
    #printf NOTF "%.6f %.6f\n", $id->{RA}, $id->{DEC};
}
